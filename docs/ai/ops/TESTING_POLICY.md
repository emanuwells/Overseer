# Testing Policy

## Filosofia

Testes devem garantir que o código funciona e que regressões são detetadas. Testes são documentação executável do comportamento esperado.

## Tipos de Testes

### Unitários

- Testam funções/métodos isolados
- Sem dependências externas (DB, rede, filesystem)
- Rápidos (< 100ms por teste)

### Integração

- Testam API e interações com DB
- Requerem serviços disponíveis
- Mais lentos, mas críticos para contratos de API

### End-to-End

- Testam fluxos completos
- Requerem ambiente completo
- Reservados para fluxos críticos

## Localização

- `tests/` — raiz do projeto
- Nomenclatura: `test_<module>_<feature>.py`
- Fixtures em `conftest.py` se necessário

## Convenção de Naming

```python
def test_<feature>_<expected_behavior>():
    """Descrição clara do teste."""
    ...
```

## Cobertura Mínima

- Lógica de domínio: 80%
- API endpoints: 100% dos happy paths
- Casos de erro: principais erros documentados

## Mocking

- Preferir fixtures reais sobre mocks
- Mock apenas dependências externas (HTTP, DB)
- Não mockar código do próprio projeto

## CI/CD

- Testes executam em cada PR
- Testes devem passar antes de merge
- Relatório de cobertura gerado

## Quando Não Testar

- Configuração trivial
- Ficheiros de dados estáticos
- Código gerado automaticamente
- Ajustes cosméticos

## Quando Testar Mais

- Lógica de negócio complexa
- Transformações de dados
- Autenticação e autorização
- Integração com serviços externos