# DISSENY VISUAL I MOCKUP - PlacetaID UI

## 🎨 Paleta de Colors (Estètica Institucional + Modern)

```
🔵 Primari Principal: #0052CC (Blau confiança)
🔵 Primari Fosc:    #003D99 (Hover, focus)
⚪ Fons Principal:    #FFFFFF (Límpid)
🩶 Fons Secundari:   #F5F7FA (Lleuger contraste)
🔤 Text Principal:   #1F2937 (Gris fosc)
🔤 Text Sec.:        #6B7280 (Gris mitjà)
🔴 Error:            #DC2626 (Advertència clara)
🟢 Èxit:             #16A34A (Confirmació)
⚠️  Avís:             #D97706 (Precaució)
```

## 📱 PANTALLA 1: LOGIN PRINCIPAL

```
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║                    🔐 PlacetaID                                    ║
║              Identificació Segura de la Placeta                    ║
║              ─────────────────────────────────                    ║
║                                                                    ║
║  Has sol·licitat accés de seguretat des de:                       ║
║  📍 loteria.laplaceta.org                                         ║
║                                                                    ║
║  ┌────────────────────────────────────────────────────────────┐  ║
║  │                                                            │  ║
║  │  📋 DIP (Document d'Identitat Personal)                   │  ║
║  │  ┌──────────────────────────────────────────────────────┐ │  ║
║  │  │                                                      │ │  ║
║  │  │  ______  -  ______  -  ______                       │ │  ║
║  │  │  (4 dig)   (4 dig)   (Control)                      │ │  ║
║  │  │                                                      │ │  ║
║  │  └──────────────────────────────────────────────────────┘ │  ║
║  │  ℹ️ Exemple: 1234-5678-A                                 │  ║
║  │                                                            │  ║
║  │  ──────────────────────────────────────────────────────── │  ║
║  │                                                            │  ║
║  │  🔐 Codi d'Autenticador (2FA)                            │  ║
║  │  ┌──────────────────────────────────────────────────────┐ │  ║
║  │  │                                                      │ │  ║
║  │  │  ______  ______  (6 dígits del teu generador)       │ │  ║
║  │  │                                                      │ │  ║
║  │  │  🔄 Si no tens generador: Utilitza SMS              │ │  ║
║  │  │     📱 +34 6XX-XXX-XXX                              │ │  ║
║  │  │     [📧 O rebre'l per email]                        │ │  ║
║  │  │                                                      │ │  ║
║  │  └──────────────────────────────────────────────────────┘ │  ║
║  │                                                            │  ║
║  │  ⚠️  LA SEGURETAT COMENÇA AQUÍ                             │  ║
║  │  • Els teus dadata no s'emmagatzemen                      │  ║
║  │  • Només validem i redirigim                             │  ║
║  │  • Mai compartirem els teus codis                        │  ║
║  │                                                            │  ║
║  │  ┌──────────────────────────────────────────────────────┐ │  ║
║  │  │ [VALIDAR I ACCEDIR]                                 │ │  ║
║  │  │ Botó: Blau intens, text blanc, 48px altura          │ │  ║
║  │  └──────────────────────────────────────────────────────┘ │  ║
║  │                                                            │  ║
║  │  🔗 [No tinc generador 2FA?]  [Problemes de accés?]      │  ║
║  │                                                            │  ║
║  └────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║  Política de Privacitat | Termes de Servei | Contacte Seguretat  ║
║  © 2026 La Placeta. Tots els drets reservats                      ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

### Especificacions Tècniques - Pantalla Login:

**Layout:**
- Margin: 32px (mobile: 16px)
- Màxim amplada: 600px, centrada
- Font: "Inter", "Segoe UI", sans-serif
- Alçada formulari: ~560px

**Camp DIP:**
- 3 camps de 4 dígits (autocompleta entre camps)
- Validació en temps real (suma de verificació espanyola)
- Foco automàtic al camp següent
- Mascara: `____-____-_`

**Camp 2FA:**
- 6 digits solament
- Espais automàtics: `___ ___`
- Countdown visual (temps restant 30s)
- Botó SMS/Email amb toggle

**Botó Validar:**
- Amplada: 100%
- Padding: 14px
- Border-radius: 8px
- Font weight: 600
- Transició smooth (200ms)
- Hover: Fons més fosc + subrelleu

**Responsive:**
- Desktop (>640px): 600px max
- Tablet (480-640px): 90vw
- Mobile (<480px): 100% - 16px

---

## 📱 PANTALLA 2: VALIDACIÓ EN PROGRÉS

```
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║                    🔐 PlacetaID                                    ║
║                                                                    ║
║                 ⏳ Validant les teves credencials...              ║
║                                                                    ║
║            ┌─────────────────────────────────────────┐            ║
║            │                                         │            ║
║            │    [████████░░░░░░░░░░] 40%             │            ║
║            │                                         │            ║
║            │    Validant DIP...                      │            ║
║            │    ⏱️ 2 segons                          │            ║
║            │                                         │            ║
║            └─────────────────────────────────────────┘            ║
║                                                                    ║
║  No tanquis aquest navegador                                      ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

---

## ❌ PANTALLA 3: ERROR - INTENT FALLAT

```
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║                    🔐 PlacetaID                                    ║
║                                                                    ║
║        ╔════════════════════════════════════════════════╗          ║
║        ║  ❌ Credencials Incorrectes                   ║          ║
║        ║                                               ║          ║
║        ║  Els dades que has introduït no coincideixen║          ║
║        ║  amb els nostres registres.                ║          ║
║        ║                                               ║          ║
║        ║  📊 Intent: 1 de 3                          ║          ║
║        ║  ⏲️ Intents restants: 2                     ║          ║
║        ║                                               ║          ║
║        ║  💡 Consells:                               ║          ║
║        ║  • Comprova que has introduït bé el DIP     ║          ║
║        ║  • Verifica el codi del teu 2FA (6 dígits)  ║          ║
║        ║  • Si usques SMS, comprova la rebuda        ║          ║
║        ║                                               ║          ║
║        ║  [← TORNAR A INTENTAR]  [AJUDA]            ║          ║
║        ║                                               ║          ║
║        ╚════════════════════════════════════════════════╝          ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

### Especificacions:
- **Tipus Card**: Bootstrap alert danger
- **Icon**: SVG `❌`
- **Fons**: #FEE2E2 (rosa pàl·lid)
- **Borde**: 2px solid #DC2626
- **Text**: #7F1D1D (rojo oscuro)
- **Animation**: Entrada suau amb wobble lligero

---

## 🚫 PANTALLA 4: COMPTE BLOCAT (TRES INTENTS)

```
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║                    🔐 PlacetaID                                    ║
║                                                                    ║
║                  ╔═══════════════════════════════╗                ║
║                  ║  🔒 COMPTE TEMPORALMENT         ║               ║
║                  ║      BLOCAT                     ║               ║
║                  ╚═══════════════════════════════╝                ║
║                                                                    ║
║  Hem detectat 3 intents incorrectes de accés al teu compte.       ║
║                                                                    ║
║  📌 INFORMACIÓ DEL BLOQUEIG:                                      ║
║  ────────────────────────────────────────────────────────         ║
║  • Raó: Massa intents fallits de validació                       ║
║  • DIP Afectat: 1234-5678-A                                       ║
║  • Bloqueig fins: 29/03/2026 - 14:32:17                          ║
║                                                                    ║
║  ⏳ TEMPS RESTANT: 23h 47m 12s ⏱️                                 ║
║  [████░░░░░░░░░░░] 24 hores (2% donat)                          ║
║                                                                    ║
║  ╔════════════════════════════════════════════════════════════╗  ║
║  ║                                                            ║  ║
║  ║  ✋ QUÈ HE DE FER ARA?                                     ║  ║
║  ║                                                            ║  ║
║  ║  1️⃣  Espera 24 hores i intent novament                     ║  ║
║  ║                                                            ║  ║
║  ║  2️⃣  O desbloqueig immediatament contactant la Seu        ║  ║
║  ║     Electrònica (recomanat per a casos urgents)           ║  ║
║  ║                                                            ║  ║
║  ║     🌐 seu.laplaceta.org/unlock                           ║  ║
║  ║     📞 900 123 456                                         ║  ║
║  ║     📧 suport@laplaceta.org                               ║  ║
║  ║                                                            ║  ║
║  ║  3️⃣  Si no és tu, reporta activitat sospitosa:            ║  ║
║  ║     🚨 seu.laplaceta.org/report-fraud                    ║  ║
║  ║                                                            ║  ║
║  ╚════════════════════════════════════════════════════════════╝  ║
║                                                                    ║
║  📊 DETALLS DEL COMPTE:                                           ║
║  • IP del darrer intent: 192.168.1.100                           ║
║  • Dispositiu: Desktop - Chrome 120 / Windows                    ║
║  • Intent des de: 192.168.1.100 fa 2 minuts                    ║
║                                                                    ║
║  💡 CONSELL DE SEGURETAT:                                         ║
║  Si no has fet aquests intents, confirma que:                    ║
║  ✓ La teva contrasenya del 2FA és segura                        ║
║  ✓ Ningú més té accés al teu generador 2FA                     ║
║  ✓ El teu dispositiu no està compromès                         ║
║                                                                    ║
║  ┌────────────────────────────────────────────────────────────┐  ║
║  │  [← TORNAR A LA WEB ORIGINAL]                             │  ║
║  └────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║  Footer: Privacitat | Seguretat | Contacte | Estad. Legal       ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

### Especificacions:
- **Fons Alert**: #FEF2F2 (beige privato)
- **Borde**: 3px solid #DC2626
- **Icon**: 🔒 grande
- **Countdown**: Actualización cada segundo
- **Color barra**: Gradient rojo → naranja
- **Botones**: Dos opcions (desblocar web | tornar)

---

## ✅ PANTALLA 5: PROCÉS D'AUTENTICACIÓ EXITÓS

```
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║                    🔐 PlacetaID                                    ║
║                                                                    ║
║              ╔═════════════════════════════════════╗              ║
║              ║    ✅ AUTENTICACIÓ REEIXIDA!       ║              ║
║              ║                                   ║              ║
║              ║    Hola, Joan Martí García!       ║              ║
║              ╚═════════════════════════════════════╝              ║
║                                                                    ║
║  📋 INFORMACIÓ D'ACCÉS:                                           ║
║  ──────────────────────────────────────────────────────           ║
║  • Nom: Joan Martí García                                        ║
║  • Nivell de Maduresa: Tier 2 (Major de 18)                     ║
║  • Aplicació: loteria.laplaceta.org                             ║
║  • Token de Sessió: Generat correctament ✓                      ║
║                                                                    ║
║              🔄 Redirigint-te a la web original...                ║
║                                                                    ║
║         ┌─────────────────────────────────────────┐              ║
║         │  [███████████░░░░░░░░] Esperau...       │              ║
║         │  Tiempo restant: 3 segons               │              ║
║         │                                         │              ║
║         │  Si no es redirigeix automàticament:    │              ║
║         │  [📍 CONTINUAR A LA APLICACIÓ]          │              ║
║         └─────────────────────────────────────────┘              ║
║                                                                    ║
║  🔐 Per la teva seguretat:                                        ║
║  • Aquesta sessió és vàlida durant 24 hores                      ║
║  • Es tancarà si no hi ha activitat durant 1 hora               ║
║  • Pot renovar-se automàticament                                 ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

### Especificacions:
- **Fons Alert**: #ECFDF5 (verd pàl·lid)
- **Borde**: 2px solid #16A34A
- **Icon**: ✅ gran
- **Text**: #065F46 (verd fosc)
- **Countdown**: Regressive 5s → redirecció automàtica
- **Animació**: Pulsing subtle en el tick

---

## 📐 DISSENY RESPONSIU

### Desktop (>1024px)
```
Full page centered, max 600px, ombra suau
```

### Tablet (768-1024px)
```
90% width, padding 16px
Fonts +10% més grans
Inputs més amples
```

### Mobile (<768px)
```
100% width, padding 12px
Fonts -5%
Full height viewport
Botó floating fix en baix (FAB style)
```

---

## 🎬 ANIMACIONS I MICRO-INTERACCIONS

### Entrada de pantalla
```css
@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
duration: 400ms, easing: cubic-bezier(0.4, 0, 0.2, 1)
```

### Focus en inputs
```css
Box-shadow: 0 0 0 3px rgba(0, 82, 204, 0.1)
Border color: #0052CC
```

### Validació input
```
DIP completa → Green checkmark (✓) amb bounce animation
2FA completa → Toast "Validant..." amb spinner
Error → Shake animation + sonor suau (alert)
```

### Countdown timer
```
Color progresa: Verde → Naranja → Rojo
Font: Monospace, bold
Update: Cada 1 segon
```

---

## 🎨 TIPOGRAFIA

| Usos | Font | Size | Weight |
|------|------|------|--------|
| Títol Principal | Inter Bold | 32px | 700 |
| Subtítol | Inter Medium | 18px | 500 |
| Etiquetes form | Inter Regular | 14px | 400 |
| Inputs text | Inter Regular | 16px | 400 |
| Bottó text | Inter Semi-Bold | 16px | 600 |
| Ads pequeños | Inter Regular | 12px | 400 |
| Countdown | Courier New | 24px | 700 |

---

## ♿ Accessibilitat

✅ **WCAG 2.1 AA**
- Contrast ratio: 4.5:1 mínimo
- Teclado navigation: Tab completo
- ARIA labels en inputs
- Annnunciaments dinàmics (screen readers)
- Focus indicators visible
- Fonts legibles (16px mínimo)
- Alt text en imatges

