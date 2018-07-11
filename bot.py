import sc2
from sc2.constants import PROBE, NEXUS, ASSIMILATOR, PYLON, GATEWAY, CYBERNETICSCORE, GATEWAYTRAIN_STALKER, STALKER
from sc2 import BotAI, run_game, Race, Difficulty, maps
from sc2.player import Computer, Bot
from math import tanh

LOOPS_PER_SECOND = 22.4

class YousefBot(BotAI):
    async def on_step(self, iteration):
        self.time_passed = (self.state.game_loop / LOOPS_PER_SECOND)
        await self.distribute_workers()
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilators()
        await self.expand()
        await self.build_army_buildings()
        await self.train_army()
        await self.attack()


    async def build_workers(self):
        for nexus in self.units(NEXUS).ready.noqueue:
            if self.can_afford(PROBE):
                if nexus.assigned_harvesters < nexus.ideal_harvesters:
                    await self.do(nexus.train(PROBE))
                else:
                    for assimilator in self.units(ASSIMILATOR).ready:
                        if assimilator.assigned_harvesters < assimilator.ideal_harvesters:
                            await self.do(nexus.train(PROBE))
                            break

    async def build_pylons(self):
        if self.supply_left < 5 and not self.already_pending(PYLON):
            nexuses = self.units(NEXUS).ready
            if nexuses.exists:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=nexuses.random)


    async def build_assimilators(self):
        for nexus in self.units(NEXUS).ready:
            vespenes = self.state.vespene_geyser.closer_than(15.0, nexus)
            for vespene in vespenes:
                if not self.can_afford(ASSIMILATOR):
                    break
                worker = self.select_build_worker(vespene.position)
                if worker is None:
                    break
                if not self.units(ASSIMILATOR).closer_than(1.0, vespene).exists:
                    await self.do(worker.build(ASSIMILATOR, vespene))


    async def build_army_buildings(self):
        # minutes_passed = self.time_passed / 60
        desired_count = self.units(NEXUS).ready.amount
        if self.units(PYLON).ready.exists:
            pylon = self.units(PYLON).random
            if self.units(GATEWAY).ready.exists:
                if self.units(CYBERNETICSCORE).empty and not self.already_pending(CYBERNETICSCORE) and self.can_afford(CYBERNETICSCORE):
                    await self.build(CYBERNETICSCORE, near=pylon)
                elif self.units(GATEWAY).ready.amount < desired_count and not self.already_pending(GATEWAY) and self.can_afford(GATEWAY):
                    await self.build(GATEWAY, near=pylon)
            elif self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
                await self.build(GATEWAY, near=pylon)

    async def expand(self):
        minutes_passed = self.time_passed / 60
        desired_count = round(tanh(minutes_passed / 15)*7)
        if self.units(NEXUS).ready.amount < desired_count and not self.already_pending(NEXUS) and self.can_afford(NEXUS):
            await self.expand_now()

    async def train_army(self):
        for gw in self.units(GATEWAY).ready.noqueue:
            abilities = await self.get_available_abilities(gw)
            if GATEWAYTRAIN_STALKER in abilities and self.can_afford(STALKER):
                await self.do(gw.train(STALKER))


    async def attack(self):
        if self.units(STALKER).ready.idle.amount > 10:
            if self.known_enemy_units.amount > 0:
                for stalker in self.units(STALKER).ready.idle:
                    await self.do(stalker.attack(self.known_enemy_units.random))
            elif self.known_enemy_structures.amount > 0:
                for stalker in self.units(STALKER).ready.idle:
                    await self.do(stalker.attack(self.known_enemy_structures.random))
            else:
                for stalker in self.units(STALKER).ready.idle:
                    await self.do(stalker.attack(self.enemy_start_locations[0]))
        elif self.units(STALKER).ready.idle.amount > 3:
            if self.known_enemy_units.amount > 0 and self.known_enemy_units.closer_than(30.0, self.units(NEXUS).random).exists:
                for stalker in self.units(STALKER).ready.idle:
                    await self.do(stalker.attack(self.known_enemy_units.random))

run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, YousefBot()),
    Computer(Race.Terran, Difficulty.Easy)
], realtime=False)