# Desafio de estágio em Machine Learning / AI

Imagine que você faz parte de um time que compartilha diferentes GPUs para trabalhar com IA. Antes de começar uma tarefa, é importante saber quais recursos estão disponíveis e quando podem ser utilizados.

Neste desafio, a ideia é criar um assistente de IA conversacional que ajude a consultar essas informações de forma simples e acessível.

O usuário deverá conseguir utilizar o assistente para, pelo menos:

- Consultar informações sobre os recursos de GPU disponíveis.

Sua aplicação deve simular os seguintes recursos:

| GPU          | Quantity | Memory (GB) |
|--------------|---------:|------------:|
| NVIDIA A100  | 4        | 80          |
| NVIDIA L40S  | 6        | 48          |
| NVIDIA RTX 4090 | 3     | 24          |
| NVIDIA H100  | 2        | 80          |
| NVIDIA A40   | 4        | 48          |

O assistente deve consultar os dados da aplicação para responder perguntas sobre a infraestrutura, evitando assumir ou inventar informações que deveriam ser obtidas pelo sistema.

Não existe uma única implementação ou arquitetura correta. Prefira uma solução simples que você consiga executar, testar e explicar.

O frontend não é o foco principal deste desafio, mas sua implementação é encorajada para proporcionar uma melhor experiência de interação com o assistente.

O uso de IA e assistentes de código é permitido.

## Exemplo de interação

> **Usuário:** Quais GPUs existem na infraestrutura?
>
> **Assistente:** Temos NVIDIA A100, NVIDIA L40S, NVIDIA RTX 4090, NVIDIA H100 e NVIDIA A40.
>
> **Usuário:** Existem duas A100 disponíveis?
>
> **Assistente:** Sim, existem duas A100 disponíveis.

Este é apenas um exemplo. A forma como o assistente funciona e interage com os dados faz parte da solução.

## Entregáveis

Ao final do desafio, disponibilize:

1. Código-fonte
2. Documentação sobre as decisões tomadas e instruções para executar o projeto.

Disponibilize a solução em um repositório público no GitHub.

## Uso de modelos para o assistente

- Não é necessário utilizar serviços pagos ou APIs comerciais de IA.
- Você pode utilizar um modelo de linguagem executado localmente em sua máquina.
- Não será avaliada a capacidade ou qualidade do modelo escolhido, mas sim como ele é utilizado e integrado à solução.
- Caso alguma limitação técnica impeça a utilização de um modelo de linguagem, documente como você abordou o problema e como integraria um modelo à solução.

## Apresentação

- Você deve estar apto a apresentar a sua solução e explicá-la.
