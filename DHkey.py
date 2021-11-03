import random
class DHkey:
    def __init__(self,g,p):
        self.g = g
        self.p = p
        self.randNum = -1
        self.key = -1

    def MakeHalfKey(self,randNum = -1):
        if randNum < 0:
            print("Generating new random number")
            randNum = random.randint(2000,200000)
        self.randNum = randNum
        halfKey = (self.g ** randNum) % self.p
        return halfKey

    def MakeFullKey(self,halfKey):
        fullKey = (halfKey ** self.randNum) % self.p
        self.key = fullKey
        return fullKey

    def __str__(self):
        randNumstr = "N/A" if(self.randNum == -1) else str(self.randNum)
        keystr= "N/A" if(self.key == -1) else str(self.key)
        outstr = "g => " + str(self.g) + " p => " + str(self.p) + " randNum => " + randNumstr + " key => " + keystr
        return outstr

def main():
    g = 5
    p = 32
    #init instance
    alice = DHkey(g,p)
    bob = DHkey(g,p)

    #create half key with optional random number
    ahkey = alice.MakeHalfKey()
    bhkey = bob.MakeHalfKey(69420)

    #create full key with the other end's half key
    akey = alice.MakeFullKey(bhkey)
    bkey = bob.MakeFullKey(ahkey)

    #output for debug
    print("Alice =>\t", alice)
    print("Bob =>\t\t", bob)



if __name__ == '__main__':
    main()
