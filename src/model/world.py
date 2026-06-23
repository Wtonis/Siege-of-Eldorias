"""
World - координатор боя: владеет сущностями и связывает системы.
Не тянет в себя логику сущностей (они обновляют себя сами), а лишь задаёт
порядок шага и обрабатывает исходы: попадания снарядов, смерти, доход до базы.
Дискретные факты публикуются в EventBus; состояние view читает сам.
"""
from typing import Optional
import config
from src.core.event_bus import EventBus
from src.events import EnemyKilled, EnemyReachedBase, TowerBuilt
from src.model.entities.ballista import Ballista
from src.model.entities.bolt import Bolt
from src.model.entities.enemy import Enemy
from src.model.entities.projectile import Projectile
from src.model.entities.soldier import Soldier
from src.model.entities.tower import Tower
from src.model.level.path import Path
from src.model.level.slot import BuildSlot
from src.model.systems.damage import DamageType
from src.model.systems.economy import Economy
from src.model.systems.effects import EffectSpec
from src.model.systems.synergy import SynergySystem
from src.model.vector import Vec2


class World:
    def __init__(
        self,
        path: Path,
        slots: list[BuildSlot],
        economy: Economy,
        ballista: Ballista,
        synergy: SynergySystem,
        event_bus: EventBus,
    ) -> None:
        self.path: Path = path
        self.slots: list[BuildSlot] = slots
        self.economy: Economy = economy
        self.ballista: Ballista = ballista
        self.synergy: SynergySystem = synergy
        self.events: EventBus = event_bus

        self.enemies: list[Enemy] = []
        self.towers: list[Tower] = []
        self.projectiles: list[Projectile] = []     # только активные
        self.bolts: list[Bolt] = []                 # болты баллисты (редкие, без пула)
        self._projectile_pool: list[Projectile] = []  # неактивные для переиспользования

    # --- Команды извне (контроллер/волны) ---

    def spawn_enemy(self, enemy: Enemy) -> None:
        self.enemies.append(enemy)

    def build_tower(self, tower: Tower) -> bool:
        """Ставит башню в её слот, если он свободен и хватает золота."""
        slot = self.slots[tower.slot_index]
        if slot.occupied or not self.economy.spend(tower.stats.cost):
            return False
        slot.occupied = True
        tower.position = slot.position
        tower.invested = tower.stats.cost
        self.towers.append(tower)
        self.synergy.recompute(self.towers, self.slots)
        self.events.publish(TowerBuilt(slot.index, tower.kind))
        return True

    def tower_at(self, slot_index: int) -> Optional[Tower]:
        for tower in self.towers:
            if tower.slot_index == slot_index:
                return tower
        return None

    def upgrade_tower(self, slot_index: int) -> bool:
        """Поднимает уровень башни, если есть куда и хватает золота."""
        tower = self.tower_at(slot_index)
        if tower is None or not tower.can_upgrade:
            return False
        cost = tower.upgrade_cost
        if not self.economy.spend(cost):
            return False
        tower.upgrade()
        tower.invested += cost
        return True

    def specialize_tower(self, slot_index: int, branch_key: str) -> bool:
        """Выбирает ветку специализации башни за золото."""
        tower = self.tower_at(slot_index)
        if tower is None or not tower.can_specialize:
            return False
        cost = tower.specialization_cost(branch_key)
        if not self.economy.spend(cost):
            return False
        tower.specialize(branch_key)
        tower.invested += cost
        return True

    def sell_tower(self, slot_index: int) -> bool:
        """Продаёт башню, возвращая долю вложенного золота и освобождая слот."""
        tower = self.tower_at(slot_index)
        if tower is None:
            return False
        tower.on_sold()
        self.economy.add_gold(int(tower.invested * config.SELL_REFUND_RATIO))
        self.towers.remove(tower)
        self.slots[slot_index].occupied = False
        self.synergy.recompute(self.towers, self.slots)
        return True

    @property
    def synergy_links(self) -> set[tuple[int, int]]:
        return self.synergy.links

    @property
    def soldiers(self) -> list[Soldier]:
        """Все солдаты со всех казарм (для отрисовки)."""
        result: list[Soldier] = []
        for tower in self.towers:
            result.extend(tower.soldiers)
        return result

    def fire_ballista(self, target: Vec2) -> bool:
        """Выстрел баллисты прямой наводкой в точку (если орудие готово)."""
        if not self.ballista.fire():
            return False
        stats = self.ballista.stats
        direction = (target - self.ballista.position).normalized()
        bolt = Bolt()
        bolt.reset(self.ballista.position, direction, stats.damage, stats.damage_type,
                   stats.bolt_speed, stats.pierce, stats.range)
        self.bolts.append(bolt)
        return True

    def upgrade_ballista(self) -> bool:
        """Апгрейд баллисты за золото (урон/перезарядка/пробитие)."""
        if not self.ballista.can_upgrade:
            return False
        cost = self.ballista.upgrade_cost
        if not self.economy.spend(cost):
            return False
        self.ballista.upgrade()
        self.ballista.invested += cost
        return True

    # --- Шаг симуляции ---

    def update(self, dt: float) -> None:
        for enemy in self.enemies:
            enemy.update(dt)
        for tower in self.towers:
            tower.update(dt, self.enemies, self._spawn_projectile)
        for projectile in self.projectiles:
            projectile.update(dt)
            if projectile.has_hit:
                self._resolve_hit(projectile)
        self.ballista.update(dt)
        for bolt in self.bolts:
            bolt.update(dt)
            self._resolve_bolt(bolt)
        self._collect_outcomes()
        self._cleanup()

    # --- Внутреннее ---
    # Алгоритм переиспользования снарядов (Object pool). Берём снаряд из пула, если там есть; иначе создаём новый.
    def _spawn_projectile(
        self,
        origin: Vec2,
        target: Enemy,
        damage: int,
        damage_type: DamageType,
        speed: float,
        splash_radius: float,
        effect: Optional[EffectSpec] = None,
    ) -> None:
        projectile = self._projectile_pool.pop() if self._projectile_pool else Projectile()
        projectile.reset(origin, target, damage, damage_type, speed, splash_radius, effect)
        self.projectiles.append(projectile)

    def _resolve_hit(self, projectile: Projectile) -> None:
        if projectile.splash_radius > 0.0:
            for enemy in self.enemies:
                if enemy.alive and projectile.impact_point.distance_to(enemy.position) <= projectile.splash_radius:
                    self._hit_enemy(enemy, projectile)
        elif projectile.target is not None and projectile.target.alive:
            self._hit_enemy(projectile.target, projectile)
        projectile.active = False

    def _hit_enemy(self, enemy: Enemy, projectile: Projectile) -> None:
        enemy.take_damage(projectile.damage, projectile.damage_type)
        if projectile.effect is not None:
            enemy.apply_effect(projectile.effect)

    def _resolve_bolt(self, bolt: Bolt) -> None:
        """Болт бьёт каждого нового врага на пути, пока не кончится пробитие."""
        if not bolt.active:
            return
        for enemy in self.enemies:
            if not enemy.alive or enemy.id in bolt.hit_ids:
                continue
            if bolt.position.distance_to(enemy.position) <= enemy.stats.radius + config.BOLT_RADIUS:
                enemy.take_damage(bolt.damage, bolt.damage_type)
                bolt.hit_ids.add(enemy.id)
                bolt.pierce_remaining -= 1
                if bolt.pierce_remaining <= 0:
                    bolt.active = False
                    break

    def _collect_outcomes(self) -> None:
        """Награда за убитых и урон базе за дошедших до конца."""
        for enemy in self.enemies:
            if not enemy.alive:
                self.economy.add_gold(enemy.stats.reward)
                self.events.publish(EnemyKilled(enemy.id, enemy.stats.reward))
            elif enemy.reached_base:
                self.economy.lose_life(enemy.stats.base_damage)
                self.events.publish(EnemyReachedBase(enemy.id, enemy.stats.base_damage))

    def _cleanup(self) -> None:
        self.enemies = [e for e in self.enemies if e.alive and not e.reached_base]
        self.bolts = [b for b in self.bolts if b.active]
        still_active: list[Projectile] = []
        for projectile in self.projectiles:
            if projectile.active:
                still_active.append(projectile)
            else:
                self._projectile_pool.append(projectile)
        self.projectiles = still_active
