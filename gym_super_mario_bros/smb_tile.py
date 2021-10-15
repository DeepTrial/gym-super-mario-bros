from collections import namedtuple
import numpy as np
from enum import Enum, unique


_STATIC_LOOKUP_TABLE={
    "Empty" : (0x00,0),
    "Fake" : (0x01,10),
    "Ground0" : (0x54,1),
    "Ground1" : (0x16,1),
    "Ground2" : (0x17,1),
    "Ground3" : (0x18,1),
    "Top_Pipe0" : (0x11,2),
    "Top_Pipe1" : (0x12,2),
    "Top_Pipe2" : (0x13,2),
    "Top_Pipe3" : (0x10,2),
    "Bottom_Pipe1" : (0x14,2),
    "Bottom_Pipe2" : (0x15,2),
    "Bottom_Pipe3" : (0x1c,2),
    "Bottom_Pipe4" : (0x1d,2),
    "Bottom_Pipe5" : (0x1e,2),
    "Bottom_Pipe6" : (0x1f,2),
    "Bottom_Pipe7" : (0x20,2),
    "Bottom_Pipe8" : (0x21,2),
    "Flagpole_Top" :  (0x24,3),
    "Flagpole" : (0x25,3),
    "Coin_Block1" : (0xC0,4),
    "Coin_Block2" : (0xC1 ,4),
    "Coin_Block3" : (0xC4 ,4),
    "Coin" : (0xC2,5),
    "Breakable_Block1" : (0x51,6),
    "Breakable_Block2" : (0x52,1),
    "Breakable_Block3" : (0x53,1),
    "Breakable_Block4" : (0x58,1),
    "Breakable_Block5" : (0x57,1),
    "Breakable_Block6" : (0x5a,1),
    "Breakable_Block7" : (0x5d,1),
    "Breakable_Block8" : (0x5c,1),
    "Breakable_Block11" : (0x5e,1),
    "Breakable_Block10" : (0x54,1),
    "Breakable_Block9" : (0x23,4),
    "HighTable" : (0x61,1),
    "Invisable1" : (0x60,0),
    
    "Generic_Static_Tile" : (0xFF,-1),
}


_ENEMY_LOOKUP_TABLE={
    "Green_Koopa1" : (0x00,7),
    "Red_Koopa1"   : (0x01,7),
    "Buzzy_Beetle" : (0x02,7),
    "Red_Koopa2" : (0x03,7),
    "Green_Koopa2" : (0x04,7),
    "Hammer_Brother" : (0x05,7),
    "Goomba"      : (0x06,7),
    "Blooper" : (0x07,7),
    "Bullet_Bill" : (0x08,7),
    "Green_Koopa_Paratroopa" : (0x09,7),
    "Grey_Cheep_Cheep" : (0x0A,7),
    "Red_Cheep_Cheep" : (0x0B,7),
    "Pobodoo" : (0x0C,7),
    "Piranha_Plant" : (0x0D,7),
    "Green_Paratroopa_Jump" : (0x0E,7),
    "Bowser_Flame1" : (0x10,7),
    "Lakitu" : (0x11,7),
    "Spiny_Egg" : (0x12,7),
    "Fly_Cheep_Cheep" : (0x14,7),
    "Bowser_Flame2" : (0x15,7),
    "Generic_Enemy" : (0xFF,7),
}

class SuperMarioBrosTile():
    
    
    # SMB can only load 5 enemies to the screen at a time.
    # Because of that we only need to check 5 enemy locations
    def __init__(self,ram):
        self.ram=ram
        self._relative_mario_location_x=-1
        self._mario_location_y=-1
        self._absolute_mario_location_x=-1
        
        self.MAX_NUM_ENEMIES = 5
        self.Enemy_Drawn = 0x0F
        self.Enemy_Type = 0x16
        self.Enemy_X_Position_In_Level = 0x6E
        self.Enemy_X_Position_On_Screen = 0x87
        self.Enemy_Y_Position_On_Screen = 0xCF
        self.Enemy_X_Position_Screen_Offset = 0x3AE

        self.Player_X_Postion_In_Level       = 0x06D
        self.Player_X_Position_On_Screen     = 0x086
        self.Player_X_Position_Screen_Offset = 0x3AD
        self.Player_Y_Position_Screen_Offset = 0x3B8


    def update_info(self,rx,y,ax,last_tile):
        self._relative_mario_location_x=rx
        self._mario_location_y=y
        self._absolute_mario_location_x=ax
        self.last_tile=last_tile

    def get_game_tiles(self):
        return self._draw_game_tile()

    # MARK: Memory access
    def _search_ram(self,x,y,group_not_empty=False):
        
        page = (x // 256) % 2
        sub_x = (x % 256) // 16
        sub_y = (y - 32) // 16

        if sub_y not in range(13):
            return 0x00

        addr = 0x500 + page*208 + sub_y*16 + sub_x
        if group_not_empty:
            if self.ram[addr] != 0:
                return "Fake"

        return self.ram[addr]

    def _lookup_static_tile_type(self,tile_address):
        for tile_type in _STATIC_LOOKUP_TABLE.keys():
            if _STATIC_LOOKUP_TABLE[tile_type][0]==tile_address:
                return tile_type
        return "Dynamic"
    
    def _lookup_enemy_tile_type(self,enemy_address):
        for tile_type in _ENEMY_LOOKUP_TABLE.keys():
            if _ENEMY_LOOKUP_TABLE[tile_type][0]==enemy_address:
                return tile_type
        return "Fake"
    
    def _draw_game_tile(self):
        step=16

        # init the tile
        game_tile=np.zeros((240,256))


        # get mario location
        # from updated info
        assert self._relative_mario_location_x>0
        assert self._mario_location_y>0
        assert self._absolute_mario_location_x>0
        mario_y=256-self._mario_location_y+step
        mario_x=self._relative_mario_location_x

        # get enemy location
        enemies_location=self._get_enemy_locations()

        # draw static tile
        start_x=self._absolute_mario_location_x-self._relative_mario_location_x
        start_y=0
        for coord_y in range(start_y,240+8,8):
            for coord_x in range(start_x,start_x+256+8,8):
                tile_type="Empty"
                tile_address=self._search_ram(coord_x,coord_y)

                # PPU is there, so no tile is there
                if coord_y//step < 2:
                    tile_type="Empty"
                else:
                    tile_type=self._lookup_static_tile_type(tile_address)
                    if tile_type=='Breakable_Block9':
                        draw_x=coord_x-start_x
                        draw_y=coord_y
                        game_tile[draw_y:(draw_y+step),draw_x:(draw_x+step)] = self.last_tile[draw_y:(draw_y+step),draw_x:(draw_x+step)]
                        continue
                    if tile_type=="Dynamic":
                        draw_x=coord_x-start_x
                        draw_y=coord_y
                        game_tile[draw_y:(draw_y+step),draw_x:(draw_x+step)] = int(tile_address)
                        continue
                    
                    # if tile_type=='Fake':   # maybe invisiable block or touched coin_block
                    #     draw_x=coord_x-start_x
                    #     draw_y=coord_y
                    #     if np.sum(self.last_tile[draw_y:(draw_y+step),draw_x:(draw_x+step)],axis=(0,1))!=0: # touched coin_block
                    #         game_tile[draw_y:(draw_y+step),draw_x:(draw_x+step)] = self.last_tile[draw_y:(draw_y+step),draw_x:(draw_x+step)]
                    #         continue
                    #     else:
                    #         pass #invisable block

                draw_x=coord_x-start_x
                draw_y=coord_y
                game_tile[draw_y:(draw_y+step),max(0,draw_x):(draw_x+step)] = _STATIC_LOOKUP_TABLE[tile_type][1]
        
        # draw enemy    
        for enemy in enemies_location:
            enemy_id=enemy[0]
            enemy_name=self._lookup_enemy_tile_type(enemy_id)
            ex = enemy[1]-self._absolute_mario_location_x+self._relative_mario_location_x
            ey = enemy[2]+step//2

            if ex<0 or ey<0:
                continue

            # avoid draw the plant in the pipe or draw the invisiable enemy 
            if (enemy_name=="Piranha_Plant" and ey+step//2<240 and ex+step//2<256 and game_tile[ey+step//2,ex+step//2]!=0) or enemy_name=="Fake":
                continue
            game_tile[ey:(ey+step),ex:(ex+step)] = _ENEMY_LOOKUP_TABLE[enemy_name][1]

       
        
        game_tile[mario_y:(mario_y+step),max(0,mario_x):(mario_x+step)]=8
        return game_tile


          
    def _get_enemy_locations(self):
        # We only care about enemies that are drawn. Others may?? exist
        # in memory, but if they aren't on the screen, they can't hurt us.
        # enemies = [None for _ in range(cls.MAX_NUM_ENEMIES)]
        enemies = []

        for enemy_num in range(self.MAX_NUM_ENEMIES):
            enemy = self.ram[self.Enemy_Drawn + enemy_num]
            # Is there an enemy? 1/0
            if enemy:
                # Get the enemy X location.
                x_pos_level = self.ram[self.Enemy_X_Position_In_Level + enemy_num]
                x_pos_screen = self.ram[self.Enemy_X_Position_On_Screen + enemy_num]
                enemy_loc_x = (x_pos_level * 0x100) + x_pos_screen #- ram[0x71c]
             
                # Get the enemy Y location.
                enemy_loc_y = self.ram[self.Enemy_Y_Position_On_Screen + enemy_num]

                # Grab the id
                enemy_id = self.ram[self.Enemy_Type + enemy_num]
                # Create enemy-
                e = (enemy_id, enemy_loc_x, enemy_loc_y)

                enemies.append(e)
        return enemies

        
