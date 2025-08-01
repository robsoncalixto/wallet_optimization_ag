"""
Módulo contendo a implementação do algoritmo genético.

Esta classe implementa um algoritmo genético genérico que pode ser usado
para otimizar qualquer tipo de cromossomo.
"""

from __future__ import annotations
from typing import TypeVar, Generic, List, Callable, Tuple
from statistics import mean
from random import choices, random, uniform
from enum import Enum
import matplotlib.pyplot as plt
import pandas as pd

T = TypeVar('T', bound='Chromosome')

class GeneticAlgorithm(Generic[T]):
    """
    Implementação de um algoritmo genético genérico.
    
    Esta classe pode ser usada para otimizar qualquer tipo de cromossomo
    que implemente a interface Chromosome.
    """
    
    class SelectionType(Enum):
        """Tipos de seleção disponíveis no algoritmo genético."""
        TOURNAMENT = "tournament"
    
    def __init__(
        self,
        population: List[C],
        threshold: float,
        max_generations: int,
        mutation_rate: float,
        crossover_rate: float,
        selection_type: SelectionType = SelectionType.TOURNAMENT,
        fitness_key: Callable = None,
        elitism: bool = True
    ) -> None:
        """
        Inicializa o algoritmo genético.
        
        Args:
            population: População inicial de cromossomos
            threshold: Limiar de aptidão para parada antecipada
            max_generations: Número máximo de gerações
            mutation_rate: Taxa de mutação
            crossover_rate: Taxa de cruzamento
            selection_type: Tipo de seleção a ser usado
            fitness_key: Função para calcular aptidão
            elitism: Se deve aplicar elitismo
        """
        self._population: List[C] = population
        self._threshold: float = threshold
        self._max_generations: int = max_generations
        self._mutation_rate: float = mutation_rate
        self._crossover_rate: float = crossover_rate 
        self._selection_type: GeneticAlgorithm.SelectionType = selection_type
        self._fitness_key: Callable = fitness_key if fitness_key else lambda x: x.fitness()
        self._elitism: bool = elitism
    
    def _pick_tournament(self, competitors: int = 3) -> Tuple[C, C]:
        """
        Seleção por torneio.
        
        Args:
            competitors: Número de competidores no torneio
            
        Returns:
            Tuple[C, C]: Dois cromossomos selecionados
        """
        participants = choices(self._population, k=competitors)
        sorted_participants = sorted(participants, key=self._fitness_key, reverse=True)
        
        # Garante que sempre retornamos 2 cromossomos
        if len(sorted_participants) >= 2:
            return tuple(sorted_participants[:2])
        else:
            # Se há apenas 1 participante, duplica
            return tuple([sorted_participants[0], sorted_participants[0]])

    def _reduce_replace(self) -> None:
        """Substitui a população atual por uma nova geração."""
        new_population = []
        while len(new_population) < len(self._population):
            parents = self._pick_tournament(3)
            if random() < self._crossover_rate:
                new_population.extend(parents[0].crossover(parents[1]))
            else:
                new_population.extend(parents)
        if len(new_population) > len(self._population):
            new_population.pop()
        self._population = new_population

    def _apply_elitism(self, new_population: List[C]) -> List[C]:
        """
        Preserva os melhores indivíduos da população anterior.
        
        Args:
            new_population: Nova população gerada
            
        Returns:
            List[C]: População com elitismo aplicado
        """
        if not self._elitism:
            return new_population
        
        # Ordena população atual e nova por fitness
        self._population.sort(key=self._fitness_key, reverse=True)
        new_population.sort(key=self._fitness_key, reverse=True)
        
        # Mantém os 10% melhores da população anterior
        elite_size = max(1, len(self._population) // 10)
        elite = self._population[:elite_size]
        
        # Substitui os piores da nova população pelos melhores da anterior
        return elite + new_population[:len(self._population) - elite_size]
    
    def _mutation(self) -> None:
        """Aplica mutação na população."""
        for chromosome in self._population:
            if random() < self._mutation_rate:
                chromosome.mutate()
    
    def run(self) -> C:
        """
        Executa o algoritmo genético.
        
        Returns:
            C: Melhor cromossomo encontrado
        """
        best: C = max(self._population, key=self._fitness_key)
        gens = []
        best_fitness_list = []
        mean_fitness_list = []
        
        for generation in range(self._max_generations):
            current_best_fitness = self._fitness_key(best)
            current_mean_fitness = mean(map(self._fitness_key, self._population))
            gens.append(generation)
            best_fitness_list.append(current_best_fitness)
            mean_fitness_list.append(current_mean_fitness)
            
            if current_best_fitness >= self._threshold:
                break
                
            print(f"Generation: {generation}, Best Fitness: {current_best_fitness}, Mean Fitness: {current_mean_fitness}")
            
            self._reduce_replace()
            if self._elitism:
                self._population = self._apply_elitism(self._population)
            self._mutation()
            
            highest: C = max(self._population, key=self._fitness_key)
            if self._fitness_key(highest) > self._fitness_key(best):
                best = highest
                
        self.results = pd.DataFrame({
            "gens": gens,
            "best_fitness": best_fitness_list,
            "mean_fitness": mean_fitness_list
        })
        return best
    
    def show_results(self) -> None:
        """Exibe os resultados do algoritmo genético em um gráfico."""
        if hasattr(self, 'results'):
            df = pd.DataFrame(self.results)
            plt.figure(figsize=(10, 6))
            plt.plot(df['gens'], df['best_fitness'], label='Melhor Fitness', linewidth=2)
            plt.plot(df['gens'], df['mean_fitness'], label='Média Fitness', linestyle='--')
            plt.title("Resultados do Algoritmo Genético")
            plt.xlabel("Geração")
            plt.ylabel("Fitness")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.show()
        else:
            print("Nenhum resultado disponível. Execute o algoritmo primeiro.")
        return getattr(self, 'results', None)
