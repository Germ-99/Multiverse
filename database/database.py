import sqlite3
import aiosqlite
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="multiverse.db"):
        self.db_path = db_path
    
    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    user_id INTEGER PRIMARY KEY,
                    r6_mmr INTEGER DEFAULT 500,
                    r6_games INTEGER DEFAULT 0,
                    r6_wins INTEGER DEFAULT 0,
                    r6_losses INTEGER DEFAULT 0,
                    rl_mmr INTEGER DEFAULT 500,
                    rl_games INTEGER DEFAULT 0,
                    rl_wins INTEGER DEFAULT 0,
                    rl_losses INTEGER DEFAULT 0,
                    valorant_mmr INTEGER DEFAULT 500,
                    valorant_games INTEGER DEFAULT 0,
                    valorant_wins INTEGER DEFAULT 0,
                    valorant_losses INTEGER DEFAULT 0,
                    breachers_mmr INTEGER DEFAULT 500,
                    breachers_games INTEGER DEFAULT 0,
                    breachers_wins INTEGER DEFAULT 0,
                    breachers_losses INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS matches (
                    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_type TEXT,
                    queue_number INTEGER,
                    team1_players TEXT,
                    team2_players TEXT,
                    winner INTEGER,
                    mmr_changes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS mmr_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    game_type TEXT,
                    old_mmr INTEGER,
                    new_mmr INTEGER,
                    change_reason TEXT,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS parties (
                    party_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    party_name TEXT,
                    captain_id INTEGER,
                    member_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()
    
    async def get_player_mmr(self, user_id, game_type):
        async with aiosqlite.connect(self.db_path) as db:
            if game_type == "r6":
                cursor = await db.execute('SELECT r6_mmr FROM players WHERE user_id = ?', (user_id,))
            elif game_type == "rl":
                cursor = await db.execute('SELECT rl_mmr FROM players WHERE user_id = ?', (user_id,))
            elif game_type == "valorant":
                cursor = await db.execute('SELECT valorant_mmr FROM players WHERE user_id = ?', (user_id,))
            elif game_type == "breachers":
                cursor = await db.execute('SELECT breachers_mmr FROM players WHERE user_id = ?', (user_id,))
            
            result = await cursor.fetchone()
            if result:
                return result[0]
            else:
                await db.execute('INSERT INTO players (user_id) VALUES (?)', (user_id,))
                await db.commit()
                return 500
    
    async def update_player_mmr(self, user_id, game_type, new_mmr, reason="Game result"):
        new_mmr = max(0, new_mmr)
        old_mmr = await self.get_player_mmr(user_id, game_type)
        
        async with aiosqlite.connect(self.db_path) as db:
            if game_type == "r6":
                await db.execute('UPDATE players SET r6_mmr = ? WHERE user_id = ?', (new_mmr, user_id))
            elif game_type == "rl":
                await db.execute('UPDATE players SET rl_mmr = ? WHERE user_id = ?', (new_mmr, user_id))
            elif game_type == "valorant":
                await db.execute('UPDATE players SET valorant_mmr = ? WHERE user_id = ?', (new_mmr, user_id))
            elif game_type == "breachers":
                await db.execute('UPDATE players SET breachers_mmr = ? WHERE user_id = ?', (new_mmr, user_id))
            
            await db.execute('''
                INSERT INTO mmr_history (user_id, game_type, old_mmr, new_mmr, change_reason)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, game_type, old_mmr, new_mmr, reason))
            await db.commit()
    
    async def update_player_stats(self, user_id, game_type, won):
        async with aiosqlite.connect(self.db_path) as db:
            if game_type == "r6":
                if won:
                    await db.execute('''
                        UPDATE players SET r6_games = r6_games + 1, r6_wins = r6_wins + 1
                        WHERE user_id = ?
                    ''', (user_id,))
                else:
                    await db.execute('''
                        UPDATE players SET r6_games = r6_games + 1, r6_losses = r6_losses + 1
                        WHERE user_id = ?
                    ''', (user_id,))
            elif game_type == "rl":
                if won:
                    await db.execute('''
                        UPDATE players SET rl_games = rl_games + 1, rl_wins = rl_wins + 1
                        WHERE user_id = ?
                    ''', (user_id,))
                else:
                    await db.execute('''
                        UPDATE players SET rl_games = rl_games + 1, rl_losses = rl_losses + 1
                        WHERE user_id = ?
                    ''', (user_id,))
            elif game_type == "valorant":
                if won:
                    await db.execute('''
                        UPDATE players SET valorant_games = valorant_games + 1, valorant_wins = valorant_wins + 1
                        WHERE user_id = ?
                    ''', (user_id,))
                else:
                    await db.execute('''
                        UPDATE players SET valorant_games = valorant_games + 1, valorant_losses = valorant_losses + 1
                        WHERE user_id = ?
                    ''', (user_id,))
            elif game_type == "breachers":
                if won:
                    await db.execute('''
                        UPDATE players SET breachers_games = breachers_games + 1, breachers_wins = breachers_wins + 1
                        WHERE user_id = ?
                    ''', (user_id,))
                else:
                    await db.execute('''
                        UPDATE players SET breachers_games = breachers_games + 1, breachers_losses = breachers_losses + 1
                        WHERE user_id = ?
                    ''', (user_id,))
            await db.commit()
    
    async def get_player_stats(self, user_id, game_type):
        async with aiosqlite.connect(self.db_path) as db:
            if game_type == "r6":
                cursor = await db.execute('''
                    SELECT r6_mmr, r6_games, r6_wins, r6_losses FROM players WHERE user_id = ?
                ''', (user_id,))
            elif game_type == "rl":
                cursor = await db.execute('''
                    SELECT rl_mmr, rl_games, rl_wins, rl_losses FROM players WHERE user_id = ?
                ''', (user_id,))
            elif game_type == "valorant":
                cursor = await db.execute('''
                    SELECT valorant_mmr, valorant_games, valorant_wins, valorant_losses FROM players WHERE user_id = ?
                ''', (user_id,))
            elif game_type == "breachers":
                cursor = await db.execute('''
                    SELECT breachers_mmr, breachers_games, breachers_wins, breachers_losses FROM players WHERE user_id = ?
                ''', (user_id,))
            
            result = await cursor.fetchone()
            if result:
                return {
                    'mmr': result[0],
                    'games_played': result[1],
                    'wins': result[2],
                    'losses': result[3]
                }
            else:
                await db.execute('INSERT INTO players (user_id) VALUES (?)', (user_id,))
                await db.commit()
                return {
                    'mmr': 500,
                    'games_played': 0,
                    'wins': 0,
                    'losses': 0
                }
    
    async def save_match(self, game_type, queue_number, team1, team2, winner, mmr_changes):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO matches (game_type, queue_number, team1_players, team2_players, winner, mmr_changes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (game_type, queue_number, str(team1), str(team2), winner, str(mmr_changes)))
            await db.commit()
    
    async def create_party(self, party_name, captain_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO parties (party_name, captain_id, member_id)
                VALUES (?, ?, ?)
            ''', (party_name, captain_id, captain_id))
            await db.commit()
    
    async def add_party_member(self, party_name, captain_id, member_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO parties (party_name, captain_id, member_id)
                VALUES (?, ?, ?)
            ''', (party_name, captain_id, member_id))
            await db.commit()
    
    async def get_party_members(self, party_name, captain_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT member_id FROM parties 
                WHERE party_name = ? AND captain_id = ?
            ''', (party_name, captain_id))
            results = await cursor.fetchall()
            return [row[0] for row in results]
    
    async def get_user_parties(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT DISTINCT party_name, captain_id FROM parties 
                WHERE member_id = ?
            ''', (user_id,))
            return await cursor.fetchall()
    
    async def get_created_parties(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT DISTINCT party_name FROM parties 
                WHERE captain_id = ?
            ''', (user_id,))
            results = await cursor.fetchall()
            return [row[0] for row in results]
    
    async def delete_party(self, party_name, captain_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                DELETE FROM parties 
                WHERE party_name = ? AND captain_id = ?
            ''', (party_name, captain_id))
            await db.commit()
    
    async def remove_party_member(self, party_name, captain_id, member_id):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                DELETE FROM parties 
                WHERE party_name = ? AND captain_id = ? AND member_id = ?
            ''', (party_name, captain_id, member_id))
            await db.commit()
    
    async def is_party_captain(self, party_name, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT captain_id FROM parties 
                WHERE party_name = ? AND captain_id = ? LIMIT 1
            ''', (party_name, user_id))
            result = await cursor.fetchone()
            return result is not None
    
    async def party_exists(self, party_name, captain_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT COUNT(*) FROM parties 
                WHERE party_name = ? AND captain_id = ?
            ''', (party_name, captain_id))
            result = await cursor.fetchone()
            return result[0] > 0
    
    async def get_party_count(self, party_name, captain_id):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                SELECT COUNT(*) FROM parties 
                WHERE party_name = ? AND captain_id = ?
            ''', (party_name, captain_id))
            result = await cursor.fetchone()
            return result[0]