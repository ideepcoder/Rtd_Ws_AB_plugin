'''
//      #####   Sample_Server.py   #####
//
// Independent RTD generator server for WsRtd AmiBroker Data Plugin ( TESTING / DEMO )
//
// Python Program that runs as a Fake data generator Server.
// WsRTD data plugin connects to this server via specified IP:Port
//
// This program is NOT meant for PRODUCTION USE. IT is just a tester script.
//
///////////////////////////////////////////////////////////////////////
// Author: NSM51
// https://github.com/ideepcoder/Rtd_Ws_AB_plugin/
// https://forum.amibroker.com/u/nsm51/summary
//
// Users and possessors of this source code are hereby granted a nonexclusive, 
// royalty-free copyright license to use this code in individual and commercial software.
//
// AUTHOR ( NSM51 ) MAKES NO REPRESENTATION ABOUT THE SUITABILITY OF THIS SOURCE CODE FOR ANY PURPOSE. 
// IT IS PROVIDED "AS IS" WITHOUT EXPRESS OR IMPLIED WARRANTY OF ANY KIND. 
// AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOURCE CODE, 
// INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. 
// IN NO EVENT SHALL AUTHOR BE LIABLE FOR ANY SPECIAL, INDIRECT, INCIDENTAL, OR 
// CONSEQUENTIAL DAMAGES, OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, 
// WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, 
// ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOURCE CODE.
// 
// Any use of this source code must include the above notice, 
// in the user documentation and internal comments to the code.
'''
#Todo Turn this working server into a class
#This will allow easier creation of multiple objects. (e.g in ccxt)
#Todo Integrate and parse data from CCXT fetch_ohclv
#For historic data
#Todo Integrate websockets from ccxtpro
#For RTD data

import asyncio
import websockets
import datetime
import json
import random
import sys
import pandas as pd
import copy
from queue import Queue, Empty, Full



class PubSub:
    def __init__(self):
        self.waiter = asyncio.Future()
        self.stop_threads = False    ## global flag to send term signal

    def publish(self, value):
        waiter, self.waiter = self.waiter, asyncio.Future()
        waiter.set_result((value, self.waiter))

    async def subscribe(self):
        waiter = self.waiter
        while not self.stop_threads:
            value, waiter = await waiter
            yield value

    def __del__(self):
        return
    
    __aiter__ = subscribe




class RTDServer(PubSub):
    def __init__(self):
        super().__init__()

        try:
            sleepT = float(sys.argv[1])
            print(f'Frequency={sleepT} secs')
        except:
            sleepT = 0.9
            print(f'Frequency={sleepT} secs')

        ''' Settings '''
        self.tf              = 1      ## base time interval in min (periodicity)
        self.wsport          = 10102  ## Websocket port  10102
        self.sleepT          = sleepT ## simulate ticks generated every "n" seconds. SET IN MAIN()
        self.tCount          = 5      ## incl default 3 tickers, increase maxTicks accordingly
        self.incSym          = 0      ## set greater than 0, to simulate new quotes by this amount. IF 0, no new tickers added
        self.maXTicks        = 50     ## maximum concurrent ticks Try 1000 :) no problem

        self.KeepRunning     = True   ## True=Server remains running on client disconnect, False=Server stops on client disconnect

        ''' Globals '''
        self.addrem_list = []        ## simulate add and remove symbol command





    ## Proper way is for handler to have 2 task threads for send() and recv(),
    # in this case Handler thread work for sending.
    # Use a Queue for generator data to push, and send to pop,
    # and another for recv(). Then it is truly async

    async def handler(self, websocket ):
        print(f"client connected")

        asyncio.create_task( self.recv( websocket ) )

        ## Send() task within handler
        try:
            while( not self.stop_threads ):

                async for message in self:
                    await websocket.send( message )         ## send broadcast RTD messages

                if( self.stop_threads ):
                    raise websockets.ConnectionClosed( None, None )

        except websockets.ConnectionClosed as wc:
            ## can check reason for close here
            if not self.KeepRunning: stop_threads = True

        except ConnectionResetError:    pass

        print(f"client disconnected")
        return


    ## Recv() is blocking while processing
    ## in production, push requests to Queue and process asynchronously
    ## should not block or use same thread to process requests

    async def recv(self, websocket ):
        try:
            while( not self.stop_threads ):
                try:
                    async with asyncio.timeout(delay=0.3):
                        print("line 140")
                        mr = await websocket.recv()
                        print(mr)
                        try:
                            jo = json.loads( mr )
                            if 'cmd' in jo:
                                if 'arg' in jo:
                                    if jo['cmd']=='bfall':
                                        print( f"bfall cmd in {mr}")

                                    elif jo['cmd'] in ['bfauto', 'bffull']:
                                        print( f"bfauto cmd in {mr}")

                                        sym = jo['arg'] if ' ' not in jo['arg'] else (jo['arg'].split(' '))[0]

                                        jo['arg'] = f"y {sym} 2" if jo['cmd']=='bfauto' else f"y {sym} 5"
                                        print("Bananas")
                                        await self.broadcast( self.some_historical_data( jo ) )

                                        jo['sym'] = "addsym";   jo['arg'] = sym
                                        self.add_symbol( jo )
                                        print("Line 161")

                                    elif jo['cmd'] == 'bfsym':
                                        #Sock_send_Q.put( jo )    ## real code should use Queue as buffer, separate thread/async
                                        ##  jo = {"cmd":"bfsym", "arg":"y SYM1 3 1"}
                                        print("Apples")
                                        await self.broadcast( self.some_historical_data( jo ) )
                                        print( f"sent response\n{jo}" )

                                    elif jo['cmd'] == "addsym":
                                        print("Pears") #This flow is when active sym is clicked inthe context menue of the plugin
                                        jr = self.add_symbol( jo )
                                        await self.broadcast( jr )
                                        print( f"sent response\n{jr}" )

                                    elif jo['cmd'] == "remsym":
                                        print("oranges")
                                        jr = self.rem_symbol( jo )
                                        await self.broadcast( self.some_historical_data( jr ) )
                                        print( f"sent response\n{jr}" )

                                    else:   print( f"unknown cmd in {mr}")

                                else:   print( f"arg not found in {mr}")

                            else:   print( f"jo={mr}")

                        except ValueError as e:
                            #print(e)       ## if not JSON
                            print( mr )

                    if self.stop_threads:
                        raise websockets.ConnectionClosed( None, None )

                except TimeoutError: pass

        except websockets.ConnectionClosed as wc:
            print(f"Connection close: {wc}")
            if not self.KeepRunning: self.stop_threads = True

        except Exception as e:
            return repr(e)

        return


    def some_historical_data( self, jo ):
        '''simulate some historical data'''
        print(f"jo: {jo}")
        print("Some historical data")
        ## 10:unix timestamp,       // 11:unix millisec timestamp,
        ## 20:"20171215 091500",    // 21:"2017-12-15 09:15:00", // 22:"2017-12-15","09:15:00",
        ## 30:20171215,91500,       // 31: 20171215,0,(EoD)
        DtFormat = 30   ## {unix: 10, 11,} {str:20, 21, 22,} {int: 30(default), }

        try:
            t:str = jo['arg']
            t = t.split(' ')        ## reserved1 symbol_name date_from date_to timeframe ## to-do: make a json standard format

            ## SAMPLE using DF, how to mainpulate type etc
            hd_str =  '[["2024-06-11","10:00:00",22.1,22.5,22.1,22.8,12,0],["2024-06-12","10:05:00",22.8,22.7,22.3,22.4,28,0],\
                        ["2024-06-13","10:10:00",22.8,22.7,22.3,22.4,28,0],["2024-06-14","10:15:00",22.8,22.7,22.3,22.4,28,0],\
                        ["2024-06-15","10:20:00",22.8,22.7,22.3,22.4,28,0]]'

            df = pd.DataFrame( json.loads( hd_str) )                    ## simulate DF
            #df['oi'] = 0

            if DtFormat in [30, 31, 32]:                                ## sample conversion
                df.columns   = df.columns.astype(str)                       ## change type of columns from int to str

                df['0'] = df['0'].str.replace('-','')
                df['1'] = df['1'].str.replace(':','')
                df      = df.astype( {"0": "int32", "1": "int32"} )


            ## fail safe
            if len(t) != 3: t = ["y", "SYM2", 1]

            ## simulate error resopnse message in backfill
            if t[1]=="SYM2":
                ## SYM2 is also a bad json RTD (note)
                jsWs = {"cmd":"bfsym","code":404,"arg":"example of backfill error in "+t[1]}
                return json.dumps( jsWs, separators=(',', ':') )

            ## simulate ASCII import response message
            #elif t[1]=="SYM6":
            #    jsWs = {"cmd":"bfsym","code":200,"arg":"example ASCII import"+t[1],"file":"D:\\test_ascii_import.txt","format":"D:\\test_ascii.format"}
            #    return json.dumps( jsWs, separators=(',', ':') )

            #### This is backfill data generator, DF above just for illustration   ####

            jsWs = {'hist':t[1], 'format':"dtohlcvi"}           ## unix: "uohlcvi", you can re-arrange the fields

            ## Sample using DF.         make sure columns match the format
            #jsWs['bars'] = 0
            ## join to form json string with df output
            '''jsStr = json.dumps( jsWs, separators=(',', ':') )   ## , default=int argument
            jsStr = jsStr[:-2]
            jsStr = jsStr + df.to_json( orient="values" )
            jsStr = jsStr + '}'        
            return jsStr'''

            ### Below is a dummy historical data generator  ###
            jsWs['bars'] = []

            bfdays      = int( t[2] )   # days argument
            BarsPerDay  = 3             # no of bars to generate
            tf          = 1             # timeframe in minutes
            dt          = datetime.datetime.now()
            dt          = dt - datetime.timedelta( days=bfdays, minutes=( (bfdays+1)*BarsPerDay ) )

            i  = 0
            while i <= bfdays:
                j = 0
                while j < BarsPerDay:

                    jsWs['bars'].append( [ int( dt.strftime('%Y%m%d') ), int( dt.strftime('%H%M00') ),
                        20+self.r(),40-self.r(),10+self.r(),18+self.r(),100+self.r(100,500),0] )

                    ## Unix time example, change format string above [use u = localtime() or g=gmtime() c++]
                    #jsWs['bars'].append( [ int( dt.timestamp()), 20+r(),40-r(),10+r(),18+r(),100+r(100,500),0] )

                    dt = dt + datetime.timedelta( minutes=tf )
                    j +=1

                dt = dt + datetime.timedelta( days=1 )
                i += 1
            print("Line 287")
            return json.dumps( jsWs, separators=(',', ':') )    ## remove space else plugin will not match str

        except Exception as e:
            return repr(e)


    ## simulate subscribe
    def add_symbol(self, jo ):
        try:
            print("Adding symbol")
            print(jo)
            jr = copy.deepcopy(jo )
            print(f"jr: {jr}")
            sym = jr['arg']
            print(f"Message: {jr}")
            if sym not in self.addrem_list:
                self.addrem_list.append( sym )
                jr['code'] = 200
                jr['arg']  = sym + " subscribed ok"
            else:
                jr['code'] = 400
                jr['arg']  = sym + " already subcribed"

            return json.dumps( jr, separators=(',', ':') )
        except:
            pass

    ## simulate unsubscribe
    def rem_symbol(self, jo ):
        global addrem_list

        jr = copy.deepcopy( jo )
        sym = jr['arg']

        if sym not in addrem_list:
            jr['code'] = 400
            jr['arg']  = sym + " not subscribed"
        else:
            addrem_list.remove( sym )
            jr['code'] = 200
            jr['arg']  = sym + " unsubcribed ok"

        return json.dumps( jr, separators=(',', ':') )


    async def broadcast(self, message ):
        self.publish(message)

    def r(self,l=1,u=9): return random.randint(l, u)


    async def broadcast_messages_count(self):
        s1=s2=s3=0
        v1=v2=v3=0
        pTm = 0
        try:
            while not self.stop_threads:
                await asyncio.sleep( self.sleepT )    #simulate ticks in seconds

                dt   = datetime.datetime.now()

                t    = dt.hour*10000 + int( dt.minute/self.tf )*self.tf*100
                d    = int( dt.strftime('%Y%m%d') )


                if( pTm != t):
                    v1 =self.r(3,5); v2 =self.r(2,3); v3 =self.r(1,2); pTm = t;                    # bar vol reset
                    if( self.incSym and self.tCount <= self.maXTicks):
                        self.tCount += 1; print(self.tCount)

                else:   v1+=self.r(3,5); v2+=self.r(2,3); v3+=self.r(1,2)                          # bar vol cum

                s1+=v1; s2+=v2; s3+=v3                #total vol

                ## Open intentionally kept random, SYM2 test bad symbol

                #data = []
                ##'n', 'd', 't', 'o', 'h', 'l', 'c', 'v', 'oi', 's','pc','bs','bp','as','ap' (s=total vol, pc=prev day close bs,bp,as,ap=bid ask )
                self.r = self.r#todo come back to this if we are not getting the random data pulled htrough
                data = [{"n": "SYM1", "t":t, "d":d, "c": self.r(1,9), "o": self.r(1,9),     "h": 9, "l": 1,   "v": v1, "oi": 0, "bp": self.r(1, 5), "ap": self.r(5, 9), "s": s1, "bs":1, "as":1, "pc":1, "do":4, "dh":9, "dl":1}
                    , {"n": "", "t":t, "d":d, "c": self.r(10, 19), "o": self.r(10, 19), "h": 19, "l": 10, "v": v2, "oi": 0, "bp": self.r(10, 15), "ap": self.r(15, 19), "s": s2, "pc":10, "do":15, "dh":19, "dl":10}
                    , {"n": "SYM3", "t":t, "d":d, "c": self.r(20, 29), "o": self.r(20, 29), "h": 29, "l": 20, "v": v3, "oi": 0, "bp": self.r(20, 25), "ap": self.r(25, 29), "s": s3, "pc":22, "do":28, "dh":29, "dl":20}]

                ## Random symbol generator code
                k = 4
                while k <= min( self.tCount, self.maXTicks):
                    rec = {"n": "SYM"+str(k), "t":t, "d":d, "c": 18 + self.r(), "o": 20 + self.r(), "h": 40 - self.r(), "l": 10 + self.r(), "v": v1, "oi": 0, "bp": self.r(1, 5), "ap": self.r(5, 9), "s": s1, "bs":1, "as":1, "pc":1, "do":20, "dh":40, "dl":10}
                    data.append( rec )
                    k +=1

                ## make ticks for subscribed symbols
                for asym in self.addrem_list:
                    rec = {"n": asym, "t":t, "d":d, "c": 18 + self.r(), "o": 20 + self.r(), "h": 40 - self.r(), "l": 10 + self.r(), "v": v1, "oi": 0, "bp": self.r(1, 5), "ap": self.r(5, 9), "s": s1, "bs":1, "as":1, "pc":1, "do":20, "dh":40, "dl":10}
                    data.append( rec )

                #print( json.dumps( data, separators=(',', ':')) )
                await self.broadcast( json.dumps( data, separators=(',', ':')))  ## remove space else plugin will not match str

        except asyncio.CancelledError:  #raised when asyncio receives SIGINT from KB_Interrupt
            self.stop_threads = True
            print(f"asyncio tasks: send stop signal, wait for exit...")
            #try:
            #    await asyncio.get_running_loop().shutdown_asyncgens()
            #except RuntimeError: pass
            try:
                await asyncio.sleep( 3 )                          # these are not graceful exits.
                await asyncio.get_running_loop().stop()           # unrecco = asyncio.get_event_loop().stop()
            except: pass



    async def start_ws_server( self,aport ):
        print( f"Started RTD server: port={aport}, tf={self.tf}min, sym_count={self.tCount}, increment_sym={self.incSym}" )

        async with websockets.serve(self.handler, "localhost", aport ):
            await self.broadcast_messages_count()

        return


async def main():
    server = RTDServer()
    await asyncio.gather(server.start_ws_server(server.wsport))

if __name__ == "__main__":
    try:
        print(f"###  press ctrl+c to exit  ###")
        
        asyncio.run( main() )
        
        print(f"Exit 0")

    except KeyboardInterrupt:
        print(f"Kill signal, Exit 1")
        stop_threads = True

    except asyncio.CancelledError: pass
    except Exception: pass