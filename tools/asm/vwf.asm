; CFC2 FR : chasse variable dans l'afficheur de texte sub_205FE2.
;
; L'afficheur pose 1 glyphe par tuile : « ld WA,QWA ; call 0x2459CC ; inc H ; inc L »
; (XIX = tuile courante, avance de 16 ; H = colonne, L = tuiles utilisées ; QWA = couleurs).
; Points d'appel posés par tools/build.py :
;   0x205FE8 : call INIT ; nop x3       (à la place de « ld QHL,HL ; and BC,1FFh »)
;   0x2060A8, 0x206181, 0x2063D0, 0x206456, 0x2065A5 : call VWF ; nop x7
;
; VWF : BC = code du glyphe. B != 0 (icônes) ou C = 40h (case vide) -> glyphe d'origine dans une
; tuile entière (chasse fixe). Sinon glyphe 1 bpp de FONT, avance LARG, posé au pixel près.
; Encre = couleur A&3, fond = couleur W&3 (comme sub_2459CC). PX = pixels occupés dans la tuile
; ouverte (IX-16) ; valable seulement si IX n'a pas bougé depuis (SAVIX).
;
; Assemblage : asl -cpu 96C141 vwf.asm ; p2bin vwf.p   (tools/build.py)

        cpu     96C141
        maxmode on
        org     800000h

FONT    equ     800400h         ; 256 x 8 octets 1 bpp
LARG    equ     800C00h         ; 256 octets
EXPAND  equ     800D00h         ; 256 mots
DRAW    equ     2459CCh

PX      equ     5FF0h           ; octet
SH      equ     5FF1h           ; octet : 2 x décalage
SAVIX   equ     5FF2h           ; long
INK     equ     5FF6h           ; mot
BG      equ     5FF8h           ; mot
SH2     equ     5FFAh           ; octet : 16 - SH
FIN8    equ     5FFCh           ; long : fin du glyphe
MONOF   equ     5FFBh           ; octet : 1 = chasse fixe forcée
AFFICHE equ     205FE2h

        jp      INIT                    ; 800000h
        jp      VWF                     ; 800004h
        jp      MONOCALL                ; 800008h : sub_205FE2 en chasse fixe (grille du clavier)
        jp      MONOOBJ                 ; 80000Ch : sub_200919 (objet texte) en chasse fixe

INIT:   db      0D7h,0EEh,09Bh          ; ld QHL,HL
        db      0D9h,0CCh,0FFh,001h     ; and BC,01FFh
        ldb     (PX),0
        ret

MONOCALL:
        ldb     (MONOF),1
        call    AFFICHE
        ldb     (MONOF),0
        ret

MONOOBJ:
        ldb     (MONOF),1
        call    200919h
        ldb     (MONOF),0
        ret

VWF:    db      0D7h,0E2h,088h          ; ld WA,QWA
        cp      (MONOF),0
        jr      nz,MONO
        cp      b,0
        jr      nz,MONO
        cp      c,40h
        jr      z,MONO
        jp      PROP

MONO:   call    DRAW
        inc     1,h
        inc     1,l
        ldb     (PX),0
        ld      (SAVIX),xix
        ret

PAT:    dw      0000h,5555h,0AAAAh,0FFFFh

PROP:   push    xbc
        push    xde
        push    xiy
        push    xiz
        push    xwa
        ld      xde,(SAVIX)
        cp      xde,xix
        jr      z,P0
        ldb     (PX),0
P0:     ; couleurs : encre = A&3, fond = W&3
        ld      de,wa
        and     de,0303h
        ld      a,e
        extz    wa
        add     wa,wa
        extz    xwa
        add     xwa,PAT
        ld      bc,(xwa)
        ld      (INK),bc
        ld      a,d
        extz    wa
        add     wa,wa
        extz    xwa
        add     xwa,PAT
        ld      bc,(xwa)
        ld      (BG),bc
        ; glyphe
        ld      bc,(xsp+16)             ; BC empilé en premier
        extz    bc
        extz    xbc
        ld      xde,xbc
        add     xde,LARG
        ld      a,(xde)                 ; A = avance
        ld      xiy,xbc
        sll     3,xiy
        add     xiy,FONT                ; XIY = lignes du glyphe
        ld      xde,xiy
        add     xde,8
        ld      (FIN8),xde
        ld      b,(PX)                  ; B = décalage
        cp      b,0
        jr      nz,P3
        call    NEUVE
P3:     add     a,b                     ; A = décalage + avance
        ld      c,a
        cp      a,8
        jr      ule,P4
        call    NEUVE                   ; déborde : 2e tuile
        lda     xde,(xix-32)
        jr      P5
P4:     lda     xde,(xix-16)
P5:     ld      a,c
        cp      a,8
        jr      c,P6
        sub     a,8
P6:     ld      (PX),a
        ; décalages en bits
        ld      a,b
        add     a,a
        ld      (SH),a
        ld      c,a
        ld      a,16
        sub     a,c
        ld      (SH2),a
LIGNE:  ld      a,(xiy+)
        extz    wa
        add     wa,wa
        extz    xwa
        add     xwa,EXPAND
        ld      bc,(xwa)                ; BC = masque (pixel 0 en bits 15-14)
        ld      iz,bc
        ld      a,(SH)
        cp      a,0
        jr      z,SANS
        srl     a,bc                    ; partie gauche -> tuile ouverte
        ld      a,(SH2)
        sll     a,iz                    ; partie qui déborde -> tuile suivante
        jr      ECRIT
SANS:   ld      iz,0
ECRIT:  ld      wa,(INK)
        xor     wa,(xde)
        and     wa,bc
        xor     (xde),wa
        ld      wa,(INK)
        xor     wa,(xde+16)
        and     wa,iz
        xor     (xde+16),wa
        inc     2,xde
        cp      xiy,(FIN8)
        jr      nz,LIGNE
        ld      (SAVIX),xix
        pop     xwa
        pop     xiz
        pop     xiy
        pop     xde
        pop     xbc
        ret

; tuile neuve en IX (fond), IX += 16, H++, L++ ; garde A, B, C
NEUVE:  push    wa
        push    bc
        ld      wa,(BG)
        ld      b,8
N1:     ld      (xix+),wa
        djnz    b,N1
        inc     1,h
        inc     1,l
        pop     bc
        pop     wa
        ret
