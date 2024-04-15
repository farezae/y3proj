from random import randint
import time
import asyncio

'''
Generator: A function which returns a generator iterator. 
It looks like a normal function except that it contains yield expressions 
for producing a series of values usable in a for-loop or that can be 
retrieved one at a time with the next() function.
'''

# generator; generate values - producer
def odds(start,stop):
    # generator; uses yield - returns first value, pauses and then resumes in the next call
    for num in range(start,stop+1,2):
        yield num 



''' 
Coroutine: Coroutines are a more generalized form of subroutines. 
Subroutines are entered at one point and exited at another point. 
Coroutines can be entered, exited, and resumed at many different points
We may suspend a coroutineA and wait for it to execute coroutineB using the 'await()' expression
Once the coroutineB has finished executing, we may resume coroutineA from the point it was paused.
'''

# coroutines; consume values - consumer, a function that can be suspended and resumed 
def syncRandom():
    time.sleep(3) 
    return randint(1,10)
    
async def asyncRandom(): 
    await asyncio.sleep(1)


async def main():

    g2 = odds (3,15) # this is an iterator object; each yeild will temporarily suspend
    print (list(g2)) #causes generator to run until exhaustion

    
    coroutineObj = asyncRandom() # create a coroutine object
    await asyncRandom() # execute coroutine 

    loop = asyncio.new_event_loop()
    print (loop)

    




# runs main function
if __name__ == "__main__":
    asyncio.run(main())


