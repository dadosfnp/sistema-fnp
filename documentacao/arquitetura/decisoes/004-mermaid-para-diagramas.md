# RDA-004: Mermaid.js para diagramas de arquitetura versionáveis

**Status:** Aceita  
**Data:** 2026-03-24  
**Decisor:** Equipe de Tecnologia FNP

## Contexto

A documentação de arquitetura precisa ser versionada junto com o código. Ferramentas visuais como Miro, Lucidchart ou Draw.io geram arquivos binários que não permitem `git diff` significativo.

## Decisão

**Usar Mermaid.js como ferramenta principal de diagramação. Diagramas ficam em arquivos `.md` no repositório Git.**

## Justificativa

- **Versionável**: cada mudança no diagrama é um diff legível em texto.
- **Renderiza no GitHub**: arquivos `.md` com blocos Mermaid são renderizados automaticamente.
- **Sem ferramenta extra**: não precisa de licença, conta ou programa instalado.
- **Revisão em PR**: mudanças arquiteturais passam por revisão de código como qualquer código.
- **Tipos suportados**: fluxograma, sequência, ERD, C4, gantt, classe, estado — cobre tudo que precisamos.

## Complementos

- **Python Diagrams**: para diagramas de infraestrutura/implantação (ícones de provedores de nuvem).
- **Miro/FigJam**: apenas para sessões de brainstorm ao vivo, nunca como fonte de verdade. Resultado sempre transcrito para Mermaid.

## Consequências

- Diagramas têm menos controle visual fino que ferramentas WYSIWYG.
- Disposições automáticas podem não ser perfeitas — aceitar trade-off em favor do versionamento.
- Equipe precisa aprender sintaxe Mermaid (curva de aprendizado de ~1 hora).
