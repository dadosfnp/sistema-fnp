# Credenciamento facial automatizado — roadmap

> O sistema atual já implementa **captura de foto** (webcam + base64) e
> **pré-credenciamento via link** (WhatsApp/e-mail). Este documento desenha
> o caminho para evoluir até reconhecimento facial automático.

## Onde estamos hoje (entregue)

1. **Captura de foto na recepção** (`/presenca/recepcao/novo/`)
   - `getUserMedia` + `<canvas>` → upload base64 → `Visita.foto`
   - Sem dependência externa
2. **Pré-credenciamento por link**
   - Secretaria cria pré-cadastro: `/presenca/credenciamento/novo/`
   - Sistema gera URL pública com token (`/presenca/pre/<token>/`)
   - Botão único envia pelo WhatsApp (`wa.me`) ou e-mail
   - Visitante abre no celular, tira foto, aceita termo LGPD
   - Recepção vê "Pronto para chegada" e confirma entrada em 1 clique
3. **Banco já guarda foto** em `Visita.foto` e `CredenciamentoPrevio.foto`
4. **Termo LGPD** aceito antes do upload (Art. 11 LGPD — biometria é dado sensível)

## Próxima fase: identificação automática (sem pagar API externa)

Tecnologia recomendada: **face-api.js** ou **MediaPipe Face Detector**

### Opção A — face-api.js (mais maduro, comunidade ativa)

```html
<script defer src="https://cdn.jsdelivr.net/npm/face-api.js/dist/face-api.min.js"></script>
```

Fluxo proposto:
1. Carregar modelos uma vez no `base.html` (tiny_face_detector + face_recognition)
2. Ao tirar foto, extrair embedding (vetor 128D) com `faceapi.computeFaceDescriptor`
3. Salvar embedding como `JSONField` em `Visita.face_embedding`
4. Na chegada do visitante: webcam → embedding → comparar com embeddings dos
   pré-credenciamentos via `faceapi.euclideanDistance` (threshold 0.6)
5. Match → preenche dados automaticamente

**Tamanho:** ~6MB de modelo (cache no browser). Inferência ~150ms em CPU.
**Privacidade:** todo o cálculo é client-side, embedding fica no nosso servidor.

### Opção B — MediaPipe Face Detector (Google)

Mais leve (~3MB) mas só faz detecção e identificação facial; melhor para
"tem um rosto na foto?" do que "qual rosto é esse?".

## Considerações LGPD obrigatórias

Biometria é **dado pessoal sensível** (Art. 5º, II da LGPD). Antes de ligar:

1. **Base legal**: consentimento explícito (já no termo) + finalidade declarada
   ("identificar você no dia da visita à sede da FNP").
2. **Retenção**: imagem e embedding apagados em até 90 dias após a visita
   (já documentado no termo). Criar comando `purgar_credenciamentos_antigos`.
3. **Direito de revogação**: botão "Apagar minha foto" no portal público,
   acessível com o mesmo token.
4. **Não vender / não compartilhar**: deixar explícito na política de privacidade.
5. **DPO**: identificar o encarregado da FNP no rodapé do termo.

## Alternativa empresarial: serviços cloud

Se a FNP quiser precisão máxima e estiver disposta a contratar:

| Serviço | Custo | Pros | Cons |
|---|---|---|---|
| AWS Rekognition | ~$1 / 1k chamadas | Alta precisão, simples | Dados saem do BR (LGPD pesado) |
| Azure Face | ~$1 / 1k chamadas | Equivalente | Dados saem do BR |
| Google Cloud Vision | ~$1.50 / 1k | Equivalente | Dados saem do BR |
| Self-hosted (DeepFace) | Servidor próprio | Dados ficam in-house | Operação mais complexa |

Para a escala da FNP (poucos milhares de visitas/ano), **face-api.js client-side
é mais que suficiente** e elimina o risco de transferência internacional de dados.

## Estimativa de esforço

- Integração face-api.js: 2 dias
- Migration + campo embedding + endpoint de match: 1 dia
- Polimento UX (preview, retake, feedback de match): 1 dia
- Testes + LGPD audit (termos, retenção, revogação): 1 dia
- **Total: ~5 dias de desenvolvimento**

## Decisão recomendada

Ativar **face-api.js** na fase seguinte ao deploy completo do MVP, depois que a
recepção da FNP estiver usando o pré-credenciamento manual e tiver dados reais
para validar o ROI da automação.
