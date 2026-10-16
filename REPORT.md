# Relatório técnico — M2.1 e M2.2

**Estudante:** IAGO FERMIANO ORSI  
**Linguagem:** Python  
**Alvo de segmentação:** Círculos brancos

## M2.1 — Máscara binária e segmentação

### Imagens e alvo

- **Imagem favorável:** `demo_favoravel_fixed.png` e `demo_favoravel_otsu.png`. Imagem sintética de teste, com fundo preto uniforme e três círculos brancos bem definidos. Como foi criada artificialmente para a atividade, não utiliza fotografia externa. É considerada favorável devido ao alto contraste entre os objetos e o fundo, sem ruído significativo.

- **Imagem difícil:** `demo_dificulade_fixed.png` e `demo_dificuldade_otsu.png`. Imagem sintética de teste com círculos brancos e uma região com grande quantidade de ruído. A principal dificuldade é a presença de muitos pixels claros que não pertencem aos círculos, podendo gerar falsos positivos e prejudicar a contagem.

- **Alvo e convenção:** identificar os círculos brancos. Na máscara binária, branco (`255`) representa o primeiro plano, incluindo os pixels classificados como pertencentes ao alvo, e preto (`0`) representa o fundo. Na imagem difícil, o ruído também pode ser classificado como primeiro plano.

### Configurações comparadas

1. **Limiar fixo:** conversão BGR para escala de cinza, com `--threshold 120` e `THRESH_BINARY`. Pixels com intensidade superior a 120 ficam brancos; os demais ficam pretos.

2. **Otsu:** conversão BGR para escala de cinza e cálculo automático do limiar. O método procura um valor que separe os níveis de intensidade em duas classes.

### Tabela de resultados

As proporções foram calculadas dividindo a quantidade de pixels brancos pelo total de pixels. As imagens possuem resolução de `480 × 360`, totalizando `172.800` pixels.

| Imagem | Método | Parâmetros | Pixels brancos | Proporção de primeiro plano |
|---|---|---|---:|---:|
| Favorável | Fixed | `threshold=120` | 11.831 | 0,0685 (6,85%) |
| Favorável | Otsu | Limiar automático | 11.831 | 0,0685 (6,85%) |
| Difícil | Fixed | `threshold=120` | 19.920 | 0,1153 (11,53%) |
| Difícil | Otsu | Limiar automático | 74.822 | 0,4330 (43,30%) |

### Figuras e discussão

#### a) Quando o limiar fixo funcionou ou falhou

Na imagem favorável, o limiar fixo funcionou bem, pois os três círculos aparecem brancos sobre o fundo preto e estão bem definidos. O método de Otsu produziu a mesma quantidade de pixels brancos nessa imagem.

Na imagem difícil, o limiar fixo classificou parte do ruído como primeiro plano, mas manteve grande parte da região ruidosa preta. Já o método de Otsu classificou uma quantidade muito maior de pixels como brancos, incluindo muitos pixels de ruído. Portanto, a maior quantidade de pixels brancos não significa que a segmentação foi mais precisa.

#### b) Parâmetro mais sensível

O comportamento mais sensível foi observado na imagem difícil. A escolha do método alterou a proporção de primeiro plano de `11,53%` para `43,30%`, uma diferença de `54.902` pixels brancos. Isso demonstra que a segmentação depende da distribuição das intensidades e do limiar escolhido.

Na imagem favorável, os dois métodos produziram a mesma quantidade de pixels brancos, mostrando que, nesse caso, a escolha do método teve pouca influência no resultado.

#### c) Erros que atrapalham a contagem

Os falsos positivos ocorrem quando pixels do fundo ou do ruído são classificados como objetos. Os falsos negativos acontecem quando partes dos objetos são removidas, podendo fragmentá-los ou apagá-los. Além disso, quando regiões ruidosas se conectam, podem ser contadas como componentes grandes em vez de partículas separadas.

A proporção de primeiro plano é uma medida quantitativa da máscara, não uma medida de acurácia. Sem uma máscara de referência, a qualidade da segmentação pode ser avaliada visualmente, mas não é possível determinar objetivamente sua precisão.

## M2.2 — Componentes conexos e sequência morfológica

### Procedimento e parâmetros

A entrada da análise foi a máscara binária produzida na etapa de segmentação. A sequência aplicada foi **abertura → fechamento**, utilizando um elemento estruturante elíptico de `3 × 3` pixels e uma iteração por estágio.

A abertura tende a remover pequenas partículas e ruídos. O fechamento tende a preencher pequenos furos e unir pequenas interrupções. Os efeitos dependem do tamanho e da proximidade dos objetos, e as operações podem apagar detalhes ou unir regiões que deveriam permanecer separadas.

Foi utilizado o parâmetro `--min-area 20`, mantendo como selecionados os componentes com área mínima de 20 pixels. A conectividade final foi 8.

### Conectividade

Na conectividade 4, apenas os vizinhos horizontais e verticais são considerados conectados. Na conectividade 8, os vizinhos diagonais também são considerados conectados.

Na máscara difícil produzida pelo método de Otsu, foram encontrados `3.013` componentes com conectividade 4 e `1.121` componentes com conectividade 8. A diferença ocorre porque pixels que se tocam apenas pelas diagonais podem ser considerados componentes separados na conectividade 4, mas conectados na conectividade 8.

### Tabela antes/depois

| Imagem | Etapa | Componentes brutos | Componentes mantidos | Área branca (px) |
|---|---|---:|---:|---:|
| Favorável | Inicial | 3 | — | 11.831 |
| Favorável | Final | 3 | 3 | 11.831 |
| Difícil (Otsu) | Inicial | 1.121 | — | 74.822 |
| Difícil (Otsu) | Final | 167 | 28 | 66.005 |

Na tabela, **componentes brutos** representa o total detectado antes do filtro por área. **Componentes mantidos** representa os componentes com área mínima de 20 pixels. A área branca da etapa final corresponde aos pixels brancos da máscara final, antes de considerar apenas os componentes selecionados pelo filtro de área.

### Interpretação e limitações

#### Caso em que a sequência ajudou

Na imagem favorável, os três círculos permaneceram separados após a abertura e o fechamento. A quantidade de componentes e a área branca permaneceram iguais, indicando que os objetos eram suficientemente grandes e bem definidos para não sofrerem alterações significativas com as operações morfológicas utilizadas.

#### Caso em que prejudicou ou não separou

Na imagem difícil segmentada por Otsu, a abertura e o fechamento reduziram a quantidade de componentes brutos de `1.121` para `167`, e a área branca diminuiu de `74.822` para `66.005` pixels.

Mesmo após o processamento, ainda restaram 167 componentes brutos, dos quais 28 passaram pelo filtro de área mínima. Isso mostra que a morfologia reduziu parte do ruído, mas não eliminou todas as regiões indesejadas.

A soma das áreas dos componentes brutos corresponde aos pixels brancos da máscara analisada antes do filtro por área. O parâmetro `--min-area` altera a indicação de quais componentes são mantidos, mas não modifica a máscara final.

Os componentes detectados não correspondem necessariamente ao número real de objetos. Contato entre regiões, fragmentação, sobreposição e falhas de segmentação podem alterar a contagem. Neste experimento, a imagem favorável contém três círculos, enquanto a imagem difícil apresenta ruído suficiente para gerar muitos componentes adicionais.

### Conclusão

Os resultados mostram que a segmentação por limiar fixo e por Otsu pode funcionar de forma semelhante em imagens com alto contraste e fundo uniforme, mas apresentar diferenças expressivas em imagens com ruído.

A análise de componentes conexos permite quantificar as regiões detectadas, enquanto a abertura e o fechamento podem reduzir ruídos e corrigir pequenas falhas. Entretanto, essas operações não garantem a separação correta dos objetos.

Para avaliar a precisão de maneira objetiva, seria necessário comparar os resultados com uma máscara de referência previamente construída.