-- ============================================================================
-- PlacetaID Gateway - Esquema de Base de Dades
-- ============================================================================

-- Taula: Citizens (Ciutadans del registre)
CREATE TABLE citizens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    dip_encrypted VARCHAR(255) NOT NULL UNIQUE,  -- DIP xifrat
    dip_hash VARCHAR(64) NOT NULL UNIQUE,         -- SHA256(DIP) per validació
    full_name VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    age_tier ENUM('0', '1', '2') DEFAULT '0',    -- 0: Menor de 14, 1: 14-17, 2: Major de 18
    email VARCHAR(255),
    phone_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_dip_hash (dip_hash),
    INDEX idx_created_at (created_at)
);

-- Taula: 2FA Authenticators (Codi 2FA per ciutadà)
CREATE TABLE authenticators_2fa (
    id INT PRIMARY KEY AUTO_INCREMENT,
    citizen_id INT NOT NULL,
    secret_encrypted VARCHAR(255) NOT NULL,      -- Secret xifrat del generador 2FA
    backup_codes_encrypted JSON,                  -- Codis de backup xifrats
    authenticator_type ENUM('TOTP', 'SMS', 'EMAIL') DEFAULT 'TOTP',
    phone_number_for_sms VARCHAR(20),            -- Si usar SMS
    email_for_notification VARCHAR(255),         -- Si usar EMAIL
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (citizen_id) REFERENCES citizens (id) ON DELETE CASCADE,
    INDEX idx_citizen_id (citizen_id),
    UNIQUE KEY uk_citizen_type (citizen_id, authenticator_type)
);

-- Taula: Login Attempts (Registre de intents de login)
CREATE TABLE login_attempts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    citizen_id INT,                              -- NULL si desconegut (DIP no valid)
    dip_hash VARCHAR(64),                        -- Per rastrejar intents per DIP fals
    ip_address VARCHAR(45) NOT NULL,             -- IPv4 o IPv6
    user_agent VARCHAR(500),
    attempt_stage ENUM('DIP_VALIDATION', '2FA_VALIDATION', 'SUCCESS') DEFAULT 'DIP_VALIDATION',
    success BOOLEAN DEFAULT FALSE,
    error_code VARCHAR(50),                       -- 'INVALID_DIP', 'INVALID_2FA', etc.
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (citizen_id) REFERENCES citizens (id) ON DELETE SET NULL,
    INDEX idx_citizen_id (citizen_id),
    INDEX idx_ip_address (ip_address),
    INDEX idx_attempted_at (attempted_at),
    INDEX idx_dip_hash (dip_hash)
);

-- Taula: Account Lockouts (Registre de bloqueigs de compte)
CREATE TABLE account_lockouts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    citizen_id INT,                              -- NULL per bloqueig per IP
    dip_hash VARCHAR(64),                        -- Si bloqueig per DIP fals
    ip_address VARCHAR(45),                      -- Si bloqueig per força bruta per IP
    lockout_reason ENUM('MAX_ATTEMPTS', 'SUSPICIOUS_ACTIVITY', 'MANUAL') 
        DEFAULT 'MAX_ATTEMPTS',
    failed_attempts INT DEFAULT 3,
    locked_until TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unlock_token VARCHAR(64),                    -- Token per desbloquejar de seu
    
    FOREIGN KEY (citizen_id) REFERENCES citizens (id) ON DELETE SET NULL,
    INDEX idx_citizen_id (citizen_id),
    INDEX idx_ip_address (ip_address),
    INDEX idx_locked_until (locked_until)
);

-- Taula: OAuth Clients (Aplicacions auto. a usar PlacetaID)
CREATE TABLE oauth_clients (
    id INT PRIMARY KEY AUTO_INCREMENT,
    client_id VARCHAR(100) NOT NULL UNIQUE,      -- 'loteria', 'notaries', etc.
    client_secret_hashed VARCHAR(255) NOT NULL, -- Hash de secret
    app_name VARCHAR(255) NOT NULL,
    app_description TEXT,
    app_icon_url VARCHAR(500),
    redirect_uris JSON NOT NULL,                 -- URLs autoritzades de callback
    allowed_scopes JSON,                         -- ['profile', 'age-tier', etc.]
    rate_limit_per_hour INT DEFAULT 1000,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_client_id (client_id)
);

-- Taula: Authorization Codes (Codis temporals per intercanvi de token)
CREATE TABLE authorization_codes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(64) NOT NULL UNIQUE,            -- Codi aleatori
    citizen_id INT NOT NULL,
    client_id VARCHAR(100) NOT NULL,
    redirect_uri VARCHAR(500) NOT NULL,          -- URI de redirecció verificada
    scope VARCHAR(500),                          -- Scopes autoritzats
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,               -- Vàlid només 5 minuts
    
    FOREIGN KEY (citizen_id) REFERENCES citizens (id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES oauth_clients (client_id) ON DELETE CASCADE,
    UNIQUE KEY uk_code (code),
    INDEX idx_created_at (created_at),
    INDEX idx_expires_at (expires_at)
);

-- Taula: Session Tokens (JWT emmagatzemats per validació)
CREATE TABLE session_tokens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    token_hash VARCHAR(64) NOT NULL UNIQUE,      -- SHA256(token)
    citizen_id INT NOT NULL,
    client_id VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_used_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    revoked_at TIMESTAMP NULL,
    
    FOREIGN KEY (citizen_id) REFERENCES citizens (id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES oauth_clients (client_id) ON DELETE CASCADE,
    INDEX idx_token_hash (token_hash),
    INDEX idx_citizen_id (citizen_id),
    INDEX idx_expires_at (expires_at),
    INDEX idx_is_active (is_active)
);

-- Taula: Refresh Tokens (Per renovar JWT sense fer login novament)
CREATE TABLE refresh_tokens (
    id INT PRIMARY KEY AUTO_INCREMENT,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    session_token_id INT NOT NULL,
    citizen_id INT NOT NULL,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP NULL,
    
    FOREIGN KEY (session_token_id) REFERENCES session_tokens (id) ON DELETE CASCADE,
    FOREIGN KEY (citizen_id) REFERENCES citizens (id) ON DELETE CASCADE,
    INDEX idx_token_hash (token_hash),
    INDEX idx_expires_at (expires_at)
);

-- Taula: Audit Log (Registre complet de totes les accions sensibles)
CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    event_type ENUM(
        'LOGIN_ATTEMPT',
        'LOGIN_SUCCESS',
        'LOGIN_FAILED',
        'ACCOUNT_LOCKED',
        'ACCOUNT_UNLOCKED',
        'TOKEN_ISSUED',
        'TOKEN_REVOKED',
        'TOKEN_EXPIRED',
        '2FA_ENABLED',
        '2FA_DISABLED',
        'PASSWORD_CHANGED',
        'AUTHORIZATION_GRANTED',
        'AUTHORIZATION_DENIED'
    ) NOT NULL,
    citizen_id INT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    event_data JSON,                             -- Dades addicionals de l'event
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (citizen_id) REFERENCES citizens (id) ON DELETE SET NULL,
    INDEX idx_event_type (event_type),
    INDEX idx_citizen_id (citizen_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_ip_address (ip_address)
);

-- ============================================================================
-- VISTES ÚTILS
-- ============================================================================

-- Vista: Situació actual de bloqueigs
CREATE VIEW v_active_lockouts AS
SELECT 
    al.id,
    al.citizen_id,
    c.full_name,
    c.dip_hash,
    al.ip_address,
    al.lockout_reason,
    al.failed_attempts,
    al.locked_until,
    TIMESTAMPDIFF(MINUTE, NOW(), al.locked_until) as minutes_remaining
FROM account_lockouts al
LEFT JOIN citizens c ON al.citizen_id = c.id
WHERE al.locked_until > NOW()
ORDER BY al.locked_until DESC;

-- Vista: Activitat de login sospitosa (últim dia)
CREATE VIEW v_suspicious_login_activity AS
SELECT 
    ip_address,
    COUNT(*) as failed_attempts,
    COUNT(DISTINCT citizen_id) as affected_users,
    MAX(attempted_at) as last_attempt,
    GROUP_CONCAT(DISTINCT error_code) as error_codes
FROM login_attempts
WHERE success = FALSE 
  AND attempted_at > DATE_SUB(NOW(), INTERVAL 1 DAY)
GROUP BY ip_address
HAVING failed_attempts > 10
ORDER BY failed_attempts DESC;

-- Vista: Tokens actius per usuari
CREATE VIEW v_active_tokens_by_user AS
SELECT 
    c.id,
    c.full_name,
    c.email,
    COUNT(st.id) as active_tokens,
    MAX(st.last_used_at) as last_activity,
    JSON_ARRAYAGG(JSON_OBJECT(
        'client_id', st.client_id,
        'issued_at', st.issued_at,
        'expires_at', st.expires_at
    )) as tokens_info
FROM citizens c
LEFT JOIN session_tokens st ON c.id = st.citizen_id AND st.is_active = TRUE
WHERE st.expires_at > NOW()
GROUP BY c.id, c.full_name, c.email;

-- ============================================================================
-- PROCEDIMENTS EMMAGATZEMATS
-- ============================================================================

-- Procediment: Registrar intent de login
DELIMITER //
CREATE PROCEDURE sp_record_login_attempt(
    IN p_dip_hash VARCHAR(64),
    IN p_ip_address VARCHAR(45),
    IN p_user_agent VARCHAR(500),
    IN p_attempt_stage VARCHAR(50),
    IN p_success BOOLEAN,
    IN p_error_code VARCHAR(50)
)
BEGIN
    DECLARE v_citizen_id INT;
    
    -- Obtenir citizen_id si DIP és vàlid
    SELECT id INTO v_citizen_id FROM citizens 
    WHERE dip_hash = p_dip_hash 
    LIMIT 1;
    
    -- Inserir intent
    INSERT INTO login_attempts (
        citizen_id, dip_hash, ip_address, user_agent,
        attempt_stage, success, error_code
    ) VALUES (
        v_citizen_id, p_dip_hash, p_ip_address, p_user_agent,
        p_attempt_stage, p_success, p_error_code
    );
    
    -- Si no és exitós i superior a 3 intents, bloquejar
    IF NOT p_success THEN
        DECLARE v_failed_count INT;
        SELECT COUNT(*) INTO v_failed_count
        FROM login_attempts
        WHERE dip_hash = p_dip_hash
          AND success = FALSE
          AND attempted_at > DATE_SUB(NOW(), INTERVAL 24 HOUR);
        
        IF v_failed_count >= 3 THEN
            INSERT INTO account_lockouts (
                citizen_id, dip_hash, lockout_reason, failed_attempts, locked_until
            ) VALUES (
                v_citizen_id, p_dip_hash, 'MAX_ATTEMPTS', 
                v_failed_count, DATE_ADD(NOW(), INTERVAL 24 HOUR)
            );
            
            INSERT INTO audit_logs (event_type, citizen_id, ip_address, event_data)
            VALUES ('ACCOUNT_LOCKED', v_citizen_id, p_ip_address,
                JSON_OBJECT('reason', 'MAX_ATTEMPTS', 'failed_attempts', v_failed_count));
        END IF;
    END IF;
END //
DELIMITER ;

-- Procediment: Verificar si compte està blocat
DELIMITER //
CREATE FUNCTION fn_is_account_locked(p_dip_hash VARCHAR(64))
RETURNS BOOLEAN
READS SQL DATA
BEGIN
    DECLARE v_locked INT;
    
    SELECT COUNT(*) INTO v_locked
    FROM account_lockouts
    WHERE dip_hash = p_dip_hash
      AND locked_until > NOW()
      AND is_active = TRUE;
    
    RETURN v_locked > 0;
END //
DELIMITER ;

-- Procediment: Desbloquejar compte
DELIMITER //
CREATE PROCEDURE sp_unlock_account(
    IN p_unlock_token VARCHAR(64)
)
BEGIN
    UPDATE account_lockouts
    SET locked_until = NOW() - INTERVAL 1 MINUTE
    WHERE unlock_token = p_unlock_token;
    
    IF ROW_COUNT() > 0 THEN
        INSERT INTO audit_logs (event_type, event_data)
        VALUES ('ACCOUNT_UNLOCKED', 
            JSON_OBJECT('method', 'unlock_token', 'token', p_unlock_token));
    END IF;
END //
DELIMITER ;

-- Procediment: Netejar tokens expirats
DELIMITER //
CREATE PROCEDURE sp_cleanup_expired_tokens()
BEGIN
    DELETE FROM session_tokens WHERE expires_at < NOW();
    DELETE FROM refresh_tokens WHERE expires_at < NOW();
    DELETE FROM authorization_codes WHERE expires_at < NOW();
    
    INSERT INTO audit_logs (event_type, event_data)
    VALUES ('SYSTEM_MAINTENANCE', 
        JSON_OBJECT('action', 'cleanup_expired_tokens', 'timestamp', NOW()));
END //
DELIMITER ;

