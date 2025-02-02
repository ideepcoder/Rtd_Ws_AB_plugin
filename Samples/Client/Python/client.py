'''
//      #####   Sample_Client.py   #####
//
// Independent Client-app emulator for WsRtd AmiBroker Data Plugin ( TESTING / DEMO )
//
// Python Program that runs as a Fake data generator.
// WsRTD data plugin connects to the relay server via specified IP:Port, and this client
// also connects to the relay server.
//
// This program is a template for PRODUCTION USE.
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

## Make sure to implement both recv and send, dummy if reqd. This program only sent, and was failing with keepalive timeout.
## its meant to send RTD data to Relay server.

import asyncio
import websockets
import datetime
import json
import random
import copy
import pandas as pd
from queue import Queue, Empty, Full

tf       = 1      ## base time interval in min (periodicity)
wsport   = 10101  ## WS port  10101		8765
sleepT   = 0.9    ## simulate tics in seconds
tCount   = 5      ## incl default 3 tickers, increase maxTicks accordingly
incSym   = 0      ## set greater than 0, to simulate new quotes by this amount. IF 0, no new tickers added
maXTicks = 50     ## maximum concurrent ticks Try 1000 :) no problem

''' Globals '''
stop_flag   = False
addrem_list = []            ## simulate add and remove symbol command
sock_send_Q = Queue()       ## Queue used for websocket send. Assumes only 1 Remote source. Else move to Handler
sock_recv_Q = Queue()       ## incomging Queue buffer. Assumes only 1 Remote source. Else move to Handler

def r(l=1,u=9): return random.randint(l, u)

# with the server
async def ws_client():
    global stop_flag, wsport
    print(f"WebSocket: Client Connected. {datetime.datetime.now()}")
    url = "ws://127.0.0.1:"+ str(wsport)
    # Connect to the server

    async with websockets.connect(url ) as websocket:
        global stop_flag
        global sleepT, tf, tCount, incSym, maXTicks
    
        s1=s2=s3=0
        v1=v2=v3=0
        pTm = 0

        try:    await websocket.send( "rolesend" )
        except: raise websockets.ConnectionClosed( None, None )

        asyncio.create_task( process_recv_Q() )

        asyncio.create_task( recv( websocket) )

        ## IF TRUE, This part is for testing commands and the RTD GEnerator
        ## Testing commands tcmd1 or tcmd2, IF either True, Scripts exits after sending commmand

        tcmd1 = False; sendstr = ""
        if tcmd1:
            jo = {"cmd":"bfsym","arg":"y ABC1 1"}
            sendstr = some_historical_data( jo )

        tcmd2 = False
        if tcmd2:
            tmp_dt = 20241124; tmp_tm = 101000
            #jo = {"hist":"SYM9","format":"dtohlcvi","bars":[[tmp_dt,tmp_tm,22.1,22.5,22.1,22.8,120,0]]}
            #jo = {"cmd":"bfall","code":200,"arg":"ok","file":"G:\\file.txt","format":"G:\\file.format"}
            jo = {"cmd":"addsym","arg":"ABC4"}   ## Subscribe symbol
            #jo = {"cmd":"remsym","arg":"ABC4"}   ## Subscribe symbol
            jo = {"cmd":"dbremsym","code":300,"arg":"ZZZ1"}   ## RemoveSymbolInAb
            #jo = {"cmd":"dbgetlist","code":300,"arg":""}
            sendstr = json.dumps(jo)

        if tcmd1 or tcmd2:
            await websocket.send( sendstr )
            await asyncio.sleep( 5 )        ## await any plug-in responses, important
            stop_flag = True

        ## END testing commands
        
        ## Put code for BROKER / VENDOR Library in this while loop,
        ## or create task and await here. It varies depending on their Library

        while not stop_flag:
            try:
                dt   = datetime.datetime.now()

                t    = dt.hour*10000 + int( dt.minute/tf )*tf*100
                d    = int( dt.strftime('%Y%m%d') )
                
                if( pTm != t):  
                    v1 =r(3,5); v2 =r(2,3); v3 =r(1,2); pTm = t;                    # bar vol reset
                    if( incSym and tCount <= maXTicks):
                        tCount += 1; print(tCount)
                
                else:   v1+=r(3,5); v2+=r(2,3); v3+=r(1,2)                          # bar vol cum
                
                s1+=v1; s2+=v2; s3+=v3                #total vol

                ## Open intentionally kept random, SYM2 test bad symbol

                ##'n', 'd', 't', 'o', 'h', 'l', 'c', 'v', 'oi', 's','pc','bs','bp','as','ap' (s=total vol, pc=prev day close bs,bp,as,ap=bid ask )
                data = [{"n": "SYM1", "t":t, "d":d, "c": r(1,9), "o": r(1,9),     "h": 9, "l": 1,   "v": v1, "oi": 0, "bp": r(1,5),   "ap": r(5,9),   "s": s1,"bs":1,"as":1,"pc":1,"do":4,"dh":9,"dl":1}
                    ,{"n": "", "t":t, "d":d, "c": r(10,19), "o": r(10,19), "h": 19, "l": 10, "v": v2, "oi": 0, "bp": r(10,15), "ap": r(15,19), "s": s2,"pc":10,"do":15,"dh":19,"dl":10}
                    ,{"n": "SYM3", "t":t, "d":d, "c": r(20,29), "o": r(20,29), "h": 29, "l": 20, "v": v3, "oi": 0, "bp": r(20,25), "ap": r(25,29), "s": s3,"pc":22,"do":28,"dh":29,"dl":20}]
                
                k = 4
                while k <= min( tCount, maXTicks):
                    rec = {"n": "SYM"+str(k), "t":t, "d":d, "c": 18+r(), "o": 20+r(), "h": 40-r(), "l": 10+r(), "v": v1, "oi": 0, "bp": r(1,5), "ap": r(5,9), "s": s1,"bs":1,"as":1,"pc":1,"do":20,"dh":40,"dl":10}            
                    data.append( rec )
                    k +=1

                            ## make ticks for subscribed symbols
                for asym in addrem_list:
                    rec = {"n": asym, "t":t, "d":d, "c": 18+r(), "o": 20+r(), "h": 40-r(), "l": 10+r(), "v": v1, "oi": 0, "bp": r(1,5), "ap": r(5,9), "s": s1,"bs":1,"as":1,"pc":1,"do":20,"dh":40,"dl":10}            
                    data.append( rec )


                ##print( json.dumps( data, separators=(',', ':')) )    
                await websocket.send( json.dumps( data, separators=(',', ':')))

                try:
                    rs = sock_send_Q.get( timeout=0.01 );   ## timeout quickly, don't block if empty
                    await websocket.send( rs )              ## send other messages like backfill/response cmd
                except Empty:   pass
                

            # client disconnected?
            except KeyboardInterrupt:           stop_flag = True
            except websockets.ConnectionClosed as c: print(f"Conn closed {datetime.datetime.now()} {repr(c)}"); break
            except Exception as e:              print(f"ws() Ex: {e}");       break
            except BaseException as b:          print(f"ws() bEx: {b}");       break

            await asyncio.sleep( sleepT )
        return


## Proper way is for handler to have 2 task threads for send() and recv(),
# in this case Handler thread work for sending.
# Use a Queue for generator data to push, and send to pop,
# and another for recv(). Then it is truly async

## Recv() is non-blocking, requests are pushed into Queue

async def recv( websocket):
    global stop_flag, sock_recv_Q
    try:
        while not stop_flag:
            try:
                async with asyncio.timeout(delay=0.5):
                    mr = await websocket.recv()
                    try:
                        sock_recv_Q.put_nowait( mr )
                    except Full: pass

            # client disconnected?
            except asyncio.TimeoutError:        pass
    except websockets.ConnectionClosed as e: print(f"recv() {e}") ; return
    except Exception as e:  print(f"recv() Ex: {e}");               return
    except BaseException as b:  print(f"recv() bEx: {b}");          return


'''
Implement Broker/Vendor Backfill process here
'''
def some_historical_data( jo ):
    '''simulate some historical data'''

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
        elif t[1]=="SYM6":
            jsWs = {"cmd":"bfsym","code":200,"arg":"example ASCII import"+t[1],"file":"D:\\test_ascii_import.txt","format":"D:\\test_ascii.format"}
            return json.dumps( jsWs, separators=(',', ':') )

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
                    20+r(),40-r(),10+r(),18+r(),100+r(100,500),0] )
                
                ## Unix time example, change format string above [use u = localtime() or g=gmtime() c++]
                #jsWs['bars'].append( [ int( dt.timestamp()), 20+r(),40-r(),10+r(),18+r(),100+r(100,500),0] )
                
                dt = dt + datetime.timedelta( minutes=tf )
                j +=1
            
            dt = dt + datetime.timedelta( days=1 )
            i += 1

        return json.dumps( jsWs, separators=(',', ':') )    ## remove space else plugin will not match str
    
    except Exception as e:
        return repr(e)


## simulate subscribe new symbol in Remote Server
def add_symbol( jo ):
    global addrem_list

    jr = copy.deepcopy( jo )
    sym = jr['arg']

    if sym not in addrem_list:
        addrem_list.append( sym )
        jr['code'] = 200
        jr['arg']  = sym + " subscribed ok"
    else:
        jr['code'] = 400
        jr['arg']  = sym + " already subcribed"

    return json.dumps( jr, separators=(',', ':') )


## simulate unsubscribe symbool from remote server
def rem_symbol( jo ):
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


'''
Receive() Websocket is asynchronous. This means requests do NOT block the websocket.
Messages are pushed into sock_recv_Q Queue, and this async task will process them at
its own pace. This will prevent RATE LIMITS being hit by Broker/Vendor.
'''
async def process_recv_Q():
    global stop_flag, sock_recv_Q    

    while not stop_flag:
        try:
            mr = sock_recv_Q.get_nowait()
        except Empty:
            await asyncio.sleep( 0.2 )      ## prevent hot loop
            continue

        print(mr)
        if mr == "zzc":
            print(f"kill sig rec'd")
            stop_flag = True        # stop all loops
            await asyncio.sleep(1)  # wait task complete

        try:
            jo = json.loads( mr )
            if 'cmd' in jo:
                if 'arg' in jo:
                    if jo['cmd']=='bfall':
                        print( f"bfall cmd in {mr}")
                    elif jo['cmd'] in ['bfauto', "bffull"]:
                        print( f"bfauto/bffull cmd in {mr}")
                        
                        sym = jo['arg'] if ' ' not in jo['arg'] else (jo['arg'].split(' '))[0]
                        jo['arg'] = f"y {sym} 5" if jo['cmd']=='bfull' else f"y {sym} 2"
                        
                        try:
                            sock_send_Q.put( some_historical_data( jo ) )  #; print( ret )
                        except Full: print(f"recv() Ex: send.Q full"); pass

                        jo['sym'] = "addsym"
                        jo['arg'] = sym
                        add_symbol( jo )

                    elif jo['cmd'] == 'bfsym':
                        #hist_Q.put( jo )    ## real code should use Queue as buffer, separate thread/async
                        ##  jo = {"cmd":"bfsym", "arg":"y SYM1 3 1"}
                        try:
                            sock_send_Q.put( some_historical_data( jo ) )  #; print( ret )
                        except Full: print(f"recv() Ex: send.Q full"); pass
                        print( f"sent response\n{jo}" )
                    
                    elif jo['cmd'] == "addsym":
                        try:
                            jr = add_symbol( jo )
                            sock_send_Q.put( jr )  #; print( ret )
                        except Full: print(f"recv() Ex: send.Q full"); pass
                        print( f"sent response\n{jr}" )

                    elif jo['cmd'] == "remsym":
                        try:
                            jr = rem_symbol( jo )
                            sock_send_Q.put( jr )  #; print( ret )
                        except Full: print(f"recv() Ex: send.Q full"); pass
                        print( f"sent response\n{jr}" )

                    else:   print( f"unknown cmd in {mr}")
                
                else:   print( f"arg not found in {mr}")
            
            else:   print( f"jo={mr}")

        except ValueError as e:
            #print(e)       ## if not JSON
            print( mr )




def main():
    global stop_flag
    try:
        # Start the connection
        asyncio.run( ws_client() )

    except KeyboardInterrupt:   print(f"KB exit"); stop_flag = True
    except Exception as e:      print(f"main() Ex {e}"); stop_flag = True
    except BaseException as b:  print(f"main() bEx {b}"); stop_flag = True

    print(f"client exited ok.")
    exit()


if __name__ == '__main__':
    main()

## For more comments or Documentation, see the Sample_Server.py
## This has the same functions, only difference is that this is
## a client websocket connection to relay server,
## whereas sample_server bundles both websocket relay server and client generator.