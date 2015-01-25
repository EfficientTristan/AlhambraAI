import random

#I don't remember what these are doing...
card_color = lambda c: c[0]
card_value = lambda c: int(c[1])
tile_kind = lambda t: t[0]
tile_cost = lambda t: int(t[1],16)
tile_wall = lambda t: int(t[2],16) #1 = north, 2 = east, 4 = south, 8 = west

#'f' = fountain = starting tile, no scoring)
scoring = [{'f':[], 'p':[1], 's':[2], 'a':[3], 'c':[4], 'g':[5], 't':[6]},
           {'f':[], 'p':[8,1], 's':[9,2], 'a':[10,3], 'c':[11,4], 'g':[12,5], 't':[13,6]},
           {'f':[], 'p':[16,8,1], 's':[17,9,2], 'a':[18,10,3], 'c':[19,11,4], 'g':[10,12,5], 't':[21,13,6]}]

class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0
        self.tiles = []
        self.cards = []

    def make_cost(self, cost, avail, used=None):
        if not used: used = []
        max_s = sum(avail)
        if max_s < cost: return None #impossible
        if max_s == cost: return avail #use all cards if necessary
                    
        #use single card if available
        if cost in avail:
            used.append(cost)
            return used

        #now we're looking for some combo of lower cost cards
        avail = [v for v in avail if v<cost]
        for i,v in enumerate(avail):
            navail = avail[::]
            del navail[i]
            nused = used[::]
            nused.append(v)
            return self.make_cost(cost-v, navail, nused)

    def take_turn(self, bought, table_cards):
        taken = []
        #buy exact if possible, and only exact
        for (col,t),used in bought.iteritems():
            cards_in_col = [card_value(c) for c in self.cards if card_color(c) == col]
            used = self.make_cost(tile_cost(t), cards_in_col)
            bought[(col,t)] = ["%s%d" % (col,c) for c in used] if used else []

        #take new cards at random
        taken_sum = 0
        while table_cards:
            next_card = random.choice(table_cards)
            taken_sum += card_value(next_card)
            if taken and taken_sum>5:
                break
            table_cards.remove(next_card)
            taken.append(next_card)

        return bought,taken


class Game:
    def __init__(self, players):
        self.p = players
        for cp in self.p:
            cp.tiles.append('f00')

        #component setup
        self.tiles = ['p2b', 'p3c', 'p46', 'p59', 'p61', 'p72', 'p80',
             's3e', 's43', 's5c', 's66', 's78', 's84', 's90',
             'a47', 'a59', 'a63', 'a6c', 'a76', 'a81', 'a82', 'a90', 'aa0',
             'c5d', 'c66', 'c73', 'c7c', 'c89', 'c94', 'c98', 'ca0', 'cb0',
             'g6e', 'g7d', 'g83', 'g8c', 'g89', 'g92', 'ga0', 'ga1', 'ga8', 'gb0', 'gc4',
             't7b', 't87', 't96', 't93', 't99', 'ta8', 'tb1', 'tb4', 'tb0', 'tc0', 'td2']
        random.shuffle(self.tiles)
        self.cards = [c+str(i) for c in ['o','y','g','b'] for i in range(1,10) for j in range(3)]
        random.shuffle(self.cards)
        self.discard = []
        self.table_tiles = dict((c,self.tiles.pop()) for c in ['o','y','g','b'])

        #deal cards
        low_sum, low_count = 1000, 25
        self.turn = -1
        for i,cp in enumerate(self.p):
            cur_sum, cur_count = 0, 0
            while cur_sum < 20:
                cp.cards.append(self.cards.pop())
                cur_sum += card_value(cp.cards[-1])
                cur_count += 1
            if cur_sum < low_sum or (cur_sum==low_sum and cur_count<low_count):
                self.turn = i-1 #turn incremented at beginning of loop
                low_sum, low_count = cur_sum, cur_count
        self.table_cards = [self.cards.pop() for i in range(4)]
        
        #insert None to represent scoring cards
        n = len(self.cards)
        self.cards.insert(random.randint(int(.2*n),int(.4*n)), None)
        self.cards.insert(random.randint(int(.6*n),int(.8*n))+1, None)

        self.play()

    def score(self):
        #point values for current round scoring
        c_scoring = scoring[self.rnd-1]

        #for each kind of building, count how many buildings each player has 
        counts = dict((k,[[0,i] for i in range(len(self.p))]) for k in c_scoring)
        for i,cp in enumerate(self.p):
            for t in cp.tiles:
                counts[tile_kind(t)][i][0] += 1

        #score one kind of building at a time
        for k,pcount in counts.iteritems():
            #i tracks how many players have been awarded points so far for this kind of building
            i = 0
            while i<len(c_scoring[k]):
                ith_place = []
                max_count = max(pcount)[0]
                
                #no points if nobody has this kind of tile
                if max_count == 0: break

                #store indices for all players tied for ith place
                for cp in pcount:
                    if cp[0] == max_count:
                        ith_place.append(cp[1])
                        cp[0] = 0 #if you score for 1st place you can't score again for 2nd place

                #split the points among all tied for ith place, round down
                points = sum(c_scoring[k][i:i+len(ith_place)])/len(ith_place)
                for pi in ith_place:
                    self.p[pi].score += points

                i += len(ith_place)
                
        self.rnd += 1

    def play(self):
        self.rnd = 1
        #take turns until a replacement tile can no longer be drawn
        while self.tiles or None not in self.table_tiles.values():
            self.turn += 1
            cp = self.p[self.turn%len(self.p)]

            #decide turn
            bought,taken = cp.take_turn(dict(((k,v),[]) for k,v in self.table_tiles.iteritems()), self.table_cards[::])

            #execute turn
            for (col,tile),cards_used in bought.iteritems():
                if self.table_tiles[col] <> tile:
                    print "ERROR! Tried to buy %s %s but the available tiles are %s" % (col,tile,table_tiles)
                    return
                if cards_used:
                    for c in cards_used:
                        cp.cards.remove(c)
                        self.discard.append(c)
                    cp.tiles.append(self.table_tiles[col])
                    print "%s bought tile %s using %s" % (cp.name, self.table_tiles[col], cards_used)
                    self.table_tiles[col] = self.tiles.pop() if self.tiles else None
            if len(taken) > 1 and sum(card_value(c) for c in taken) > 5:
                print "ERROR! Tried to take %s, which add up to >5." % taken
                return
            for c in taken:
                self.table_cards.remove(c)
                cp.cards.append(c)
            print "%s took card(s) %s" % (cp.name, taken)
        
            #replenish table cards
            while len(self.table_cards) < 4:
                if not self.cards:
                    random.shuffle(self.discard)
                    self.cards += self.discard
                    self.discard = []
                c = self.cards.pop()
                if not c: #scoring card
                    self.score()
                    print "SCORING ROUND %d:" % (self.rnd-1)
                    for cp2 in self.p:
                        print "    %s\t%d" % (cp2.name, cp2.score)
                    c = self.cards.pop()
                self.table_cards.append(c)
            
            
        #award remaining tiles to player with highest card sum in that color, no ties
        for col,t in self.table_tiles.iteritems():
            if not t: continue
            player_sums = [sum(card_value(c) for c in cp.cards if card_color(c) == col) for cp in self.p]
            max_sum = max(player_sums)
            max_sum_players = [pi for pi,s in enumerate(player_sums) if s == max_sum]
            if len(max_sum_players) == 1:
                self.p[max_sum_players[0]].tiles.append(self.table_tiles[col])
                print "%s won tile %s with a sum of %s %s" % (self.p[max_sum_players[0]].name, self.table_tiles[col], col, max_sum)
                self.table_tiles[col] = None
        self.score()
        winning_score = max(cp.score for cp in self.p)
        print "FINAL SCORES:"
        for cp2 in self.p:
            print "%s %s\t%d" % ('(W)' if cp2.score == winning_score else '   ', cp2.name, cp2.score)

for i in range(100):
    g = Game([Player(p) for p in ['Tristan','Brian','Jason','Mark','Andrew','Kyle']])
