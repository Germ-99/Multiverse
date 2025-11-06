import math

class MMRSystem:
    def __init__(self, db_manager):
        self.db = db_manager
        self.k_factor = 25
        self.variance = 1600
    
    def calculate_expected_score(self, player_mmr, opponent_mmr):
        return 1 / (1 + 10**((opponent_mmr - player_mmr) / 400))
    
    def calculate_mmr_change(self, player_mmr, opponent_mmr, actual_score):
        expected_score = self.calculate_expected_score(player_mmr, opponent_mmr)
        base_change = self.k_factor * (actual_score - expected_score)
        
        variance_factor = self.variance / 1600
        adjusted_change = base_change / variance_factor
        
        return round(adjusted_change)
    
    def calculate_team_average_mmr(self, team_mmrs):
        return sum(team_mmrs) / len(team_mmrs)
    
    async def calculate_team_mmr_changes(self, team1_ids, team2_ids, winning_team, game_type):
        team1_mmrs = []
        team2_mmrs = []
        
        for player_id in team1_ids:
            mmr = await self.db.get_player_mmr(player_id, game_type)
            team1_mmrs.append(mmr)
        
        for player_id in team2_ids:
            mmr = await self.db.get_player_mmr(player_id, game_type)
            team2_mmrs.append(mmr)
        
        team1_avg = self.calculate_team_average_mmr(team1_mmrs)
        team2_avg = self.calculate_team_average_mmr(team2_mmrs)
        
        mmr_changes = {}
        
        for i, player_id in enumerate(team1_ids):
            if winning_team == 1:
                change = self.calculate_mmr_change(team1_mmrs[i], team2_avg, 1)
            else:
                change = self.calculate_mmr_change(team1_mmrs[i], team2_avg, 0)
            mmr_changes[player_id] = change
        
        for i, player_id in enumerate(team2_ids):
            if winning_team == 2:
                change = self.calculate_mmr_change(team2_mmrs[i], team1_avg, 1)
            else:
                change = self.calculate_mmr_change(team2_mmrs[i], team1_avg, 0)
            mmr_changes[player_id] = change
        
        return mmr_changes
    
    async def apply_mmr_changes(self, mmr_changes, game_type, reason="Match result"):
        for player_id, change in mmr_changes.items():
            current_mmr = await self.db.get_player_mmr(player_id, game_type)
            new_mmr = max(0, current_mmr + change)
            await self.db.update_player_mmr(player_id, game_type, new_mmr, reason)
    
    async def balance_teams(self, player_ids, game_type):
        player_mmrs = []
        for player_id in player_ids:
            mmr = await self.db.get_player_mmr(player_id, game_type)
            player_mmrs.append((player_id, mmr))
        
        player_mmrs.sort(key=lambda x: x[1], reverse=True)
        
        team1 = []
        team2 = []
        team1_mmr = 0
        team2_mmr = 0
        
        for player_id, mmr in player_mmrs:
            if team1_mmr <= team2_mmr:
                team1.append(player_id)
                team1_mmr += mmr
            else:
                team2.append(player_id)
                team2_mmr += mmr
        
        return team1, team2