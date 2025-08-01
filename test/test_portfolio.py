"""
Testes para o módulo portfolio.py

Este módulo contém testes abrangentes para a classe Portfolio,
incluindo testes de funcionalidade, cálculos financeiros e comportamento
como cromossomo genético.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Adiciona o diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio import Portfolio
from chromosome import Chromosome


class TestPortfolioInitialization:
    """Testes para inicialização da classe Portfolio."""
    
    def setup_method(self):
        """Configuração inicial para cada teste."""
        # Cria dados de retorno mock
        np.random.seed(42)  # Para reprodutibilidade
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        self.returns_data = pd.DataFrame({
            'PETR4.SA': np.random.normal(0.001, 0.02, 100),
            'VALE3.SA': np.random.normal(0.0015, 0.025, 100),
            'ITUB4.SA': np.random.normal(0.0008, 0.018, 100),
            '^BVSP': np.random.normal(0.0005, 0.015, 100)
        }, index=dates)
        
        self.weights = {
            'PETR4.SA': 0.3,
            'VALE3.SA': 0.4,
            'ITUB4.SA': 0.3
        }
    
    def test_inicializar_basico(self):
        """Testa inicialização básica do Portfolio."""
        portfolio = Portfolio(self.weights, self.returns_data)
        
        assert portfolio._weights == self.weights
        pd.testing.assert_frame_equal(portfolio.returns, self.returns_data)
        assert portfolio.risk_free_rate == 0.2
    
    def test_inicializar_com_taxa_livre_risco_customizada(self):
        """Testa inicialização com taxa livre de risco customizada."""
        custom_rate = 0.05
        portfolio = Portfolio(self.weights, self.returns_data, custom_rate)
        
        assert portfolio.risk_free_rate == custom_rate
    
    def test_inicializar_com_pesos_vazios(self):
        """Testa inicialização com pesos vazios."""
        empty_weights = {}
        portfolio = Portfolio(empty_weights, self.returns_data)
        
        assert portfolio._weights == empty_weights
    
    def test_inicializar_com_pesos_zero(self):
        """Testa inicialização com pesos zero."""
        zero_weights = {'PETR4.SA': 0.0, 'VALE3.SA': 0.0}
        portfolio = Portfolio(zero_weights, self.returns_data)
        
        assert portfolio._weights == zero_weights
    
    def test_heranca_de_chromosome(self):
        """Testa se Portfolio herda corretamente de Chromosome."""
        portfolio = Portfolio(self.weights, self.returns_data)
        assert isinstance(portfolio, Chromosome)


class TestPortfolioWeightsProperty:
    """Testes para a propriedade weights do Portfolio."""
    
    def setup_method(self):
        """Configuração inicial para cada teste."""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        self.returns_data = pd.DataFrame({
            'PETR4.SA': np.random.normal(0.001, 0.02, 50),
            'VALE3.SA': np.random.normal(0.0015, 0.025, 50)
        }, index=dates)
    
    def test_normalizacao_pesos(self):
        """Testa normalização dos pesos."""
        weights = {'PETR4.SA': 30, 'VALE3.SA': 70}  # Soma = 100
        portfolio = Portfolio(weights, self.returns_data)
        
        normalized = portfolio.weights
        expected = {'PETR4.SA': 0.3, 'VALE3.SA': 0.7}
        
        assert abs(normalized['PETR4.SA'] - expected['PETR4.SA']) < 1e-7
        assert abs(normalized['VALE3.SA'] - expected['VALE3.SA']) < 1e-7
        assert abs(sum(normalized.values()) - 1.0) < 1e-7
    
    def test_normalizacao_pesos_escala_diferente(self):
        """Testa normalização com escala diferente."""
        weights = {'PETR4.SA': 3, 'VALE3.SA': 7}  # Soma = 10
        portfolio = Portfolio(weights, self.returns_data)
        
        normalized = portfolio.weights
        assert abs(normalized['PETR4.SA'] - 0.3) < 1e-7
        assert abs(normalized['VALE3.SA'] - 0.7) < 1e-7
    
    def test_pesos_soma_zero_gera_erro(self):
        """Testa se pesos com soma zero levantam erro."""
        weights = {'PETR4.SA': 0, 'VALE3.SA': 0}
        portfolio = Portfolio(weights, self.returns_data)
        
        with pytest.raises(ValueError) as context:
            _ = portfolio.weights
        
        assert "soma dos valores no dicionário é zero" in str(context.value)
    
    def test_pesos_ativo_unico(self):
        """Testa normalização com um único ativo."""
        weights = {'PETR4.SA': 5.0}
        portfolio = Portfolio(weights, self.returns_data)
        
        normalized = portfolio.weights
        assert normalized['PETR4.SA'] == 1.0
    
    def test_pesos_valores_negativos(self):
        """Testa normalização com valores negativos."""
        weights = {'PETR4.SA': -2, 'VALE3.SA': 8}  # Soma = 6
        portfolio = Portfolio(weights, self.returns_data)
        
        normalized = portfolio.weights
        assert abs(normalized['PETR4.SA'] - -2/6) < 1e-7
        assert abs(normalized['VALE3.SA'] - 8/6) < 1e-7


class TestPortfolioFitness:
    """Testes para o método fitness do Portfolio."""
    
    def setup_method(self):
        """Configuração inicial para cada teste."""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        
        # Cria retornos com características conhecidas
        self.returns_data = pd.DataFrame({
            'PETR4.SA': np.random.normal(0.001, 0.02, 100),
            'VALE3.SA': np.random.normal(0.002, 0.03, 100),
            'ITUB4.SA': np.random.normal(0.0005, 0.015, 100)
        }, index=dates)
        
        self.weights = {'PETR4.SA': 0.4, 'VALE3.SA': 0.3, 'ITUB4.SA': 0.3}
        self.portfolio = Portfolio(self.weights, self.returns_data, risk_free_rate=0.1)
    
    def test_fitness_retorna_float(self):
        """Testa se fitness retorna um float."""
        fitness_value = self.portfolio.fitness()
        assert isinstance(fitness_value, (int, float))
    
    def test_fitness_com_alpha_diferente(self):
        """Testa fitness com diferentes valores de alpha."""
        fitness_95 = self.portfolio.fitness(alpha=0.95)
        fitness_99 = self.portfolio.fitness(alpha=0.99)
        
        assert isinstance(fitness_95, (int, float))
        assert isinstance(fitness_99, (int, float))
        
        # VaR com 99% de confiança deve ser mais conservador
        # Mas o fitness pode variar dependendo da implementação
    
    def test_fitness_define_retorno_esperado(self):
        """Testa se fitness calcula e armazena o retorno esperado."""
        self.portfolio.fitness()
        
        assert hasattr(self.portfolio, 'ExpReturn')
        assert isinstance(self.portfolio.ExpReturn, (int, float))
    
    def test_fitness_define_cvar(self):
        """Testa se fitness calcula e armazena o CVaR."""
        self.portfolio.fitness()
        
        assert hasattr(self.portfolio, 'cvar')
        assert isinstance(self.portfolio.cvar, (int, float))
    
    def test_fitness_cvar_negativo_ou_zero(self):
        """Testa se CVaR é negativo ou zero (representa perdas)."""
        self.portfolio.fitness()
        
        # CVaR representa perdas, então deve ser <= 0
        assert self.portfolio.cvar <= 0
    
    def test_fitness_com_taxa_livre_risco_zero(self):
        """Testa fitness com taxa livre de risco zero."""
        portfolio = Portfolio(self.weights, self.returns_data, risk_free_rate=0.0)
        fitness_value = portfolio.fitness()
        
        assert isinstance(fitness_value, (int, float))
    
    def test_fitness_com_taxa_livre_risco_alta(self):
        """Testa fitness com taxa livre de risco alta."""
        portfolio = Portfolio(self.weights, self.returns_data, risk_free_rate=0.9)
        fitness_value = portfolio.fitness()
        
        assert isinstance(fitness_value, (int, float))
    
    def test_fitness_consistencia(self):
        """Testa se fitness retorna valores consistentes."""
        fitness1 = self.portfolio.fitness()
        fitness2 = self.portfolio.fitness()
        
        assert fitness1 == fitness2


class TestPortfolioCrossover:
    """Testes para o método crossover do Portfolio."""
    
    def setup_method(self):
        """Configuração inicial para cada teste."""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
        self.returns_data = pd.DataFrame({
            'PETR4.SA': np.random.normal(0.001, 0.02, 50),
            'VALE3.SA': np.random.normal(0.002, 0.03, 50),
            'ITUB4.SA': np.random.normal(0.0005, 0.015, 50),
            'BBDC4.SA': np.random.normal(0.0012, 0.022, 50)
        }, index=dates)
        
        self.weights1 = {'PETR4.SA': 0.25, 'VALE3.SA': 0.25, 'ITUB4.SA': 0.25, 'BBDC4.SA': 0.25}
        self.weights2 = {'PETR4.SA': 0.4, 'VALE3.SA': 0.3, 'ITUB4.SA': 0.2, 'BBDC4.SA': 0.1}
        
        self.portfolio1 = Portfolio(self.weights1, self.returns_data)
        self.portfolio2 = Portfolio(self.weights2, self.returns_data)
    
    def test_crossover_retorna_tupla(self):
        """Testa se crossover retorna uma tupla."""
        result = self.portfolio1.crossover(self.portfolio2)
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_crossover_retorna_instancias_portfolio(self):
        """Testa se crossover retorna instâncias de Portfolio."""
        child1, child2 = self.portfolio1.crossover(self.portfolio2)
        
        assert isinstance(child1, Portfolio)
        assert isinstance(child2, Portfolio)
    
    def test_crossover_filhos_tem_mesmos_ativos(self):
        """Testa se os filhos têm os mesmos ativos dos pais."""
        child1, child2 = self.portfolio1.crossover(self.portfolio2)
        
        parent_keys = set(self.weights1.keys())
        child1_keys = set(child1._weights.keys())
        child2_keys = set(child2._weights.keys())
        
        assert parent_keys == child1_keys
        assert parent_keys == child2_keys
    
    def test_crossover_filhos_sao_objetos_diferentes(self):
        """Testa se os filhos são objetos diferentes dos pais."""
        child1, child2 = self.portfolio1.crossover(self.portfolio2)
        
        assert id(child1) != id(self.portfolio1)
        assert id(child1) != id(self.portfolio2)
        assert id(child2) != id(self.portfolio1)
        assert id(child2) != id(self.portfolio2)
        assert id(child1) != id(child2)
    
    def test_crossover_preserva_dados_retorno(self):
        """Testa se crossover preserva os dados de retorno."""
        child1, child2 = self.portfolio1.crossover(self.portfolio2)
        
        pd.testing.assert_frame_equal(child1.returns, self.returns_data)
        pd.testing.assert_frame_equal(child2.returns, self.returns_data)
    
    def test_crossover_preserva_taxa_livre_risco(self):
        """Testa se crossover preserva a taxa livre de risco."""
        child1, child2 = self.portfolio1.crossover(self.portfolio2)
        
        assert child1.risk_free_rate == self.portfolio1.risk_free_rate
        assert child2.risk_free_rate == self.portfolio1.risk_free_rate
    
    def test_crossover_com_taxas_livre_risco_diferentes(self):
        """Testa crossover com taxas livres de risco diferentes."""
        portfolio2_diff_rate = Portfolio(self.weights2, self.returns_data, risk_free_rate=0.15)
        
        child1, child2 = self.portfolio1.crossover(portfolio2_diff_rate)
        
        # Deve usar a taxa do primeiro pai
        assert child1.risk_free_rate == self.portfolio1.risk_free_rate
        assert child2.risk_free_rate == self.portfolio1.risk_free_rate
    
    def test_crossover_logica_ponto_medio(self):
        """Testa a lógica do ponto médio no crossover."""
        # Com 4 ativos, mid = 2
        child1, child2 = self.portfolio1.crossover(self.portfolio2)
        
        # Verifica se o crossover seguiu a lógica esperada
        assets = list(self.weights1.keys())
        mid = len(assets) // 2
        
        # Primeiros 'mid' ativos do child1 devem vir do portfolio1
        for i in range(mid):
            asset = assets[i]
            assert child1._weights[asset] == self.portfolio1._weights[asset]
        
        # Últimos ativos do child1 devem vir do portfolio2
        for i in range(mid, len(assets)):
            asset = assets[i]
            assert abs(child1._weights[asset] - self.portfolio2._weights[asset]) < 1e-10


class TestPortfolioMutate:
    """Testes para o método mutate do Portfolio."""
    
    def setup_method(self):
        """Configuração inicial para cada teste."""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        self.returns_data = pd.DataFrame({
            'PETR4.SA': np.random.normal(0.001, 0.02, 30),
            'VALE3.SA': np.random.normal(0.002, 0.03, 30)
        }, index=dates)
        
        self.weights = {'PETR4.SA': 0.6, 'VALE3.SA': 0.4}
        self.portfolio = Portfolio(self.weights, self.returns_data)
    
    def test_mutate_modifica_no_local(self):
        """Testa se mutate modifica o objeto in-place."""
        original_id = id(self.portfolio)
        original_weights = self.portfolio._weights.copy()
        
        # Força mutação com taxa alta
        self.portfolio.mutate(mutation_rate=1.0)
        
        # Verifica se é o mesmo objeto
        assert id(self.portfolio) == original_id
        
        # Verifica se os pesos foram modificados
        assert self.portfolio._weights != original_weights
    
    def test_mutate_com_taxa_zero(self):
        """Testa mutação com taxa zero."""
        original_weights = self.portfolio._weights.copy()
        
        self.portfolio.mutate(mutation_rate=0.0)
        
        # Pesos não devem ter mudado
        assert self.portfolio._weights == original_weights
    
    def test_mutate_com_taxa_completa(self):
        """Testa mutação com taxa 100%."""
        original_weights = self.portfolio._weights.copy()
        
        self.portfolio.mutate(mutation_rate=1.0)
        
        # Todos os pesos devem ter mudado
        for key in original_weights:
            assert self.portfolio._weights[key] != original_weights[key]
    
    def test_mutate_mantem_pesos_nao_negativos(self):
        """Testa se mutação mantém pesos não-negativos."""
        # Testa com pesos pequenos que poderiam ficar negativos
        small_weights = {'PETR4.SA': 0.05, 'VALE3.SA': 0.05}
        portfolio = Portfolio(small_weights, self.returns_data)
        
        portfolio.mutate(mutation_rate=1.0)
        
        # Todos os pesos devem ser >= 0
        for weight in portfolio._weights.values():
            assert weight >= 0
    
    def test_mutate_taxa_padrao(self):
        """Testa mutação com taxa padrão."""
        original_weights = self.portfolio._weights.copy()
        
        # Executa mutação várias vezes para aumentar chance de mudança
        changed = False
        for _ in range(100):
            test_portfolio = Portfolio(self.weights.copy(), self.returns_data)
            test_portfolio.mutate()  # Taxa padrão = 0.2
            
            if test_portfolio._weights != original_weights:
                changed = True
                break
        
        # Com 100 tentativas e taxa 0.2, deve ter mudado pelo menos uma vez
        assert changed
    
    def test_mutate_intervalo(self):
        """Testa se a mutação está no range esperado [-0.1, 0.1]."""
        original_weights = self.portfolio._weights.copy()
        
        # Força mutação
        self.portfolio.mutate(mutation_rate=1.0)
        
        # Verifica se as mudanças estão no range esperado
        for key in original_weights:
            change = self.portfolio._weights[key] - original_weights[key]
            assert change >= -0.1
            assert change <= 0.1


class TestPortfolioRandomInstance:
    """Testes para o método random_instance do Portfolio."""
    
    def setup_method(self):
        """Configuração inicial para cada teste."""
        np.random.seed(42)
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        self.returns_data = pd.DataFrame({
            'PETR4.SA': np.random.normal(0.001, 0.02, 30),
            'VALE3.SA': np.random.normal(0.002, 0.03, 30),
            'ITUB4.SA': np.random.normal(0.0005, 0.015, 30)
        }, index=dates)
        
        self.base_weights = {'PETR4.SA': 0.33, 'VALE3.SA': 0.33, 'ITUB4.SA': 0.34}
    
    def test_instancia_aleatoria_retorna_portfolio(self):
        """Testa se random_instance retorna uma instância de Portfolio."""
        random_portfolio = Portfolio.random_instance(
            self.base_weights, self.returns_data
        )
        
        assert isinstance(random_portfolio, Portfolio)
    
    def test_instancia_aleatoria_tem_mesmos_ativos(self):
        """Testa se instância aleatória tem os mesmos ativos."""
        random_portfolio = Portfolio.random_instance(
            self.base_weights, self.returns_data
        )
        
        base_keys = set(self.base_weights.keys())
        random_keys = set(random_portfolio._weights.keys())
        
        assert base_keys == random_keys
    
    def test_instancia_aleatoria_tem_pesos_aleatorios(self):
        """Testa se instância aleatória tem pesos diferentes."""
        random_portfolio1 = Portfolio.random_instance(
            self.base_weights, self.returns_data
        )
        random_portfolio2 = Portfolio.random_instance(
            self.base_weights, self.returns_data
        )
        
        # Probabilisticamente, devem ser diferentes
        assert random_portfolio1._weights != random_portfolio2._weights
    
    def test_instancia_aleatoria_pesos_no_intervalo(self):
        """Testa se pesos aleatórios estão no range [0, 1]."""
        random_portfolio = Portfolio.random_instance(
            self.base_weights, self.returns_data
        )
        
        for weight in random_portfolio._weights.values():
            assert weight >= 0
            assert weight <= 1
    
    def test_instancia_aleatoria_com_taxa_livre_risco_customizada(self):
        """Testa random_instance com taxa livre de risco customizada."""
        custom_rate = 0.05
        random_portfolio = Portfolio.random_instance(
            self.base_weights, self.returns_data, custom_rate
        )
        
        assert random_portfolio.risk_free_rate == custom_rate
    
    def test_instancia_aleatoria_preserva_dados_retorno(self):
        """Testa se random_instance preserva os dados de retorno."""
        random_portfolio = Portfolio.random_instance(
            self.base_weights, self.returns_data
        )
        
        pd.testing.assert_frame_equal(random_portfolio.returns, self.returns_data)


class TestPortfolioRepr:
    """Testes para o método __repr__ do Portfolio."""
    
    def setup_method(self):
        """Configuração inicial para cada teste."""
        dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
        self.returns_data = pd.DataFrame({
            'PETR4.SA': [0.01, -0.02, 0.015, -0.01, 0.005]
        }, index=dates)
        
        self.weights = {'PETR4.SA': 1.0}
        self.portfolio = Portfolio(self.weights, self.returns_data, risk_free_rate=0.1)
    
    def test_repr_retorna_string(self):
        """Testa se __repr__ retorna uma string."""
        repr_str = repr(self.portfolio)
        assert isinstance(repr_str, str)
    
    def test_repr_contem_portfolio(self):
        """Testa se __repr__ contém 'Portfolio'."""
        repr_str = repr(self.portfolio)
        assert 'Portfolio' in repr_str
    
    def test_repr_contem_pesos(self):
        """Testa se __repr__ contém informações dos pesos."""
        repr_str = repr(self.portfolio)
        # Deve conter os pesos normalizados
        assert 'PETR4.SA' in repr_str
    
    def test_repr_contem_taxa_livre_risco(self):
        """Testa se __repr__ contém a taxa livre de risco."""
        repr_str = repr(self.portfolio)
        assert '0.1' in repr_str


class TestPortfolioEdgeCases:
    """Testes para casos extremos e situações especiais."""
    
    def setup_method(self):
        """Configuração inicial para cada teste."""
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        self.returns_data = pd.DataFrame({
            'ASSET1': np.random.normal(0, 0.01, 10),
            'ASSET2': np.random.normal(0, 0.01, 10)
        }, index=dates)
    
    def test_portfolio_com_pesos_extremos(self):
        """Testa portfólio com pesos extremos."""
        weights = {'ASSET1': 1e6, 'ASSET2': 1e-6}
        portfolio = Portfolio(weights, self.returns_data)
        
        normalized = portfolio.weights
        assert abs(normalized['ASSET1'] - 1.0) < 1e-5
        assert abs(normalized['ASSET2'] - 0.0) < 1e-5
    
    def test_portfolio_com_pesos_negativos(self):
        """Testa portfólio com pesos negativos (short selling)."""
        weights = {'ASSET1': 1.5, 'ASSET2': -0.5}  # 150% long, 50% short
        portfolio = Portfolio(weights, self.returns_data)
        
        normalized = portfolio.weights
        assert abs(normalized['ASSET1'] - 1.5) < 1e-7
        assert abs(normalized['ASSET2'] - -0.5) < 1e-7
        assert abs(sum(normalized.values()) - 1.0) < 1e-7
    
    def test_portfolio_com_todos_retornos_zero(self):
        """Testa portfólio com retornos todos zero."""
        zero_returns = pd.DataFrame({
            'ASSET1': [0.0] * 10,
            'ASSET2': [0.0] * 10
        })
        
        weights = {'ASSET1': 0.5, 'ASSET2': 0.5}
        portfolio = Portfolio(weights, zero_returns)
        
        fitness_value = portfolio.fitness()
        assert isinstance(fitness_value, (int, float))
    
    def test_portfolio_com_retornos_constantes(self):
        """Testa portfólio com retornos constantes."""
        constant_returns = pd.DataFrame({
            'ASSET1': [0.01] * 10,
            'ASSET2': [0.02] * 10
        })
        
        weights = {'ASSET1': 0.5, 'ASSET2': 0.5}
        portfolio = Portfolio(weights, constant_returns)
        
        fitness_value = portfolio.fitness()
        assert isinstance(fitness_value, (int, float))
        
        # Com retornos constantes, CVaR deve ser igual ao retorno
        portfolio.fitness()
        expected_return = 0.015  # 0.5 * 0.01 + 0.5 * 0.02
        assert abs(portfolio.cvar - expected_return) < 1e-10


if __name__ == '__main__':
    # Configuração para executar os testes
    pytest.main([__file__, "-v"])
