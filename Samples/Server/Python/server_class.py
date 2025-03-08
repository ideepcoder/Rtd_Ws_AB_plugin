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
#Todo Create method Integrate and parse data from CCXT fetch_ohclv.
#For historic data, see what happens when assining to hd_str in some_historic_data
#Todo Integrate websockets from ccxtpro
#For RTD data. Look at random_generator and decipher the variable assugnments there.

import asyncio
import websockets
import datetime
import json
import random
import sys
import pandas as pd
import copy
import os
import ccxt.pro as ccxtpro
import logging
import datetime
import pytz
from queue import Queue, Empty, Full

#logging.basicConfig(level=logging.DEBUG)

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
            sleep_time = float(sys.argv[1])
            print(f'Frequency={sleep_time} secs')
        except:
            sleep_time = 0.9
            print(f'Frequency={sleep_time} secs')

        ''' Settings '''
        self.timeframe       = 1            ## base time interval in min (periodicity)
        self.websocket_port  = 10102        ## Websocket port  10102
        self.sleep_time      = sleep_time   ## simulate ticks generated every "n" seconds. SET IN MAIN()
        self.ticker_count    = 5            ## incl default 3 tickers, increase maxTicks accordingly
        self.inc_sym          = 0            ## set greater than 0, to simulate new quotes by this amount. IF 0, no new tickers added
        self.max_tickers        = 50           ## maximum concurrent ticks Try 1000 :) no problem

        self.keep_running     = True   ## True=Server remains running on client disconnect, False=Server stops on client disconnect
        self.websocket_subscription_list = []        ## simulate add and remove symbol command

        self.timezone = pytz.timezone('Australia/Perth')

        self.database = "CryptoLive"
        self.databases_path = "C:\\Program Files\\AmiBroker\\Databases\\"
        self.watchlists_path = os.path.join(self.databases_path,self.database,"WatchLists")
        self.watchlist_suffix = ".tls"


        self.exchange_instances = {
            "binance": ccxtpro.binance(),
            "bybit": ccxtpro.bybit(),
            "coinbase": ccxtpro.coinbase(),
            "okx": ccxtpro.okx(),
            "mexc":ccxtpro.mexc(),
            "kucoin":ccxtpro.kucoin(),
            "gateio":ccxtpro.gateio(),
            "kraken":ccxtpro.kraken()
        }

        self.websocket_data_list = []

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
            print(f"Websocket connection in handler: {wc}")
            if not self.keep_running: stop_threads = True

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
                    async with asyncio.timeout(3):
                        message = await websocket.recv()
                        print(f"Message from websocket: {message}")
                        try:
                            json_message = json.loads( message )
                            if 'cmd' in json_message:
                                if 'arg' in json_message:
                                    if json_message['cmd']=='bfall':
                                        print( f"bfall cmd in {message}")

                                    elif json_message['cmd'] in ['bfauto', 'bffull']:
                                        print("Bananas")
                                        sym = json_message['arg'] if ' ' not in json_message['arg'] else (json_message['arg'].split(' '))[0]
                                        json_message['arg'] = f"y {sym} 2" if json_message['cmd']=='bfauto' else f"y {sym} 5"
                                        await self.get_historic_data(json_message)
                                        json_message['sym'] = "addsym"
                                        json_message['arg'] = sym
                                        self.add_symbol(json_message)

                                    elif json_message['cmd'] == 'bfsym':
                                        print("Apples")
                                        await self.get_historic_data(json_message)

                                    elif json_message['cmd'] == "addsym":
                                        print("Pears") #This flow is when active sym is clicked in the context menu of the plugin
                                        jr = self.add_symbol( json_message )
                                        await self.broadcast( jr )

                                    elif json_message['cmd'] == "remsym":
                                        print("oranges")
                                        jr = self.rem_symbol( json_message )
                                        await self.broadcast( jr)

                                    else:
                                        print( f"unknown cmd in {message}")

                                else:
                                    print( f"arg not found in {message}")

                            else:
                                print( f"json_message={message}")

                        except ValueError as e:
                            print(f"Value error from {message}\n{e}")

                    if self.stop_threads:
                        raise websockets.ConnectionClosed( None, None )

                except TimeoutError: pass

        except websockets.ConnectionClosed as wc:
            print(f"Connection closed: {wc}")
            if not self.keep_running:
                self.stop_threads = True
        except Exception as e:
            return repr(e)
        return


    ## simulate subscribe
    def add_symbol(self, json_message):
        try:
            json_copy = copy.deepcopy(json_message)
            sym = json_copy['arg']
            if sym not in self.websocket_subscription_list:
                self.websocket_subscription_list.append(sym)
                json_copy['code'] = 200
                json_copy['arg']  = sym + " subscribed ok"
            else:
                json_copy['code'] = 400
                json_copy['arg']  = sym + " already subcribed"
            return json.dumps( json_copy, separators=(',', ':') )
        except:
            pass

    ## simulate unsubscribe
    def rem_symbol(self, json_message):

        json_copy = copy.deepcopy(json_message)
        sym = json_copy['arg']

        if sym not in self.websocket_subscription_list:
            json_copy['code'] = 400
            json_copy['arg']  = sym + " not subscribed"
        else:
            self.websocket_subscription_list.remove(sym)
            json_copy['code'] = 200
            json_copy['arg']  = sym + " unsubcribed ok"

        return json.dumps( json_copy, separators=(',', ':') )

    async def broadcast(self, message ):
        self.publish(message)

    def random_generator(self, l=1, u=9): return random.randint(l, u)


    async def broadcast_messages_count(self):
        try:
            while not self.stop_threads:
                await asyncio.sleep(self.sleep_time)    #simulate ticks in seconds
                t = 100000
                d= 20250803
                v1 = v2 = v3 = 0
                s1 = s2 = s3 = 0
                ## Open intentionally kept random, SYM2 test bad symbol
                #data = []
                ##'n', 'd', 't', 'o', 'h', 'l', 'c', 'v', 'oi', 's','pc','bs','bp','as','ap' (s=total vol, pc=prev day close bs,bp,as,ap=bid ask )
                self.random_generator = self.random_generator
                data = [
                        {
                        "n": "SYM1",
                        "t":t,
                         "d":d,
                         "c": self.random_generator(1, 9),
                         "o": self.random_generator(1, 9),
                         "h": 9,
                         "l": 1,
                         "v": v1,
                         "oi": 0,
                         "bp": self.random_generator(1, 5),
                         "ap": self.random_generator(5, 9),
                         "s": s1,
                         "bs":1,
                         "as":1,
                         "pc":1,
                         "do":4,
                         "dh":9,
                         "dl":1
                        },
                    {"n": "", "t":t, "d":d, "c": self.random_generator(10, 19), "o": self.random_generator(10, 19), "h": 19, "l": 10, "v": v2, "oi": 0, "bp": self.random_generator(10, 15), "ap": self.random_generator(15, 19), "s": s2, "pc":10, "do":15, "dh":19, "dl":10},
                    {"n": "SYM3", "t":t, "d":d, "c": self.random_generator(20, 29), "o": self.random_generator(20, 29), "h": 29, "l": 20, "v": v3, "oi": 0, "bp": self.random_generator(20, 25), "ap": self.random_generator(25, 29), "s": s3, "pc":22, "do":28, "dh":29, "dl":20}
                ]

                ## Random symbol generator code
                k = 4
                while k <= min(self.ticker_count, self.max_tickers):
                    rec = {"n": "SYM"+str(k), "t":t, "d":d, "c": 18 + self.random_generator(), "o": 20 + self.random_generator(), "h": 40 - self.random_generator(), "l": 10 + self.random_generator(), "v": v1, "oi": 0, "bp": self.random_generator(1, 5), "ap": self.random_generator(5, 9), "s": s1, "bs":1, "as":1, "pc":1, "do":20, "dh":40, "dl":10}
                    data.append( rec )
                    k +=1

                ## make ticks for subscribed symbols
                for asym in self.websocket_subscription_list:
                    rec = {"n": asym, "t":t, "d":d, "c": 18 + self.random_generator(), "o": 20 + self.random_generator(), "h": 40 - self.random_generator(), "l": 10 + self.random_generator(), "v": v1, "oi": 0, "bp": self.random_generator(1, 5), "ap": self.random_generator(5, 9), "s": s1, "bs":1, "as":1, "pc":1, "do":20, "dh":40, "dl":10}
                    data.append( rec )

                #print( json.dumps( data, separators=(',', ':')) )
                await self.broadcast( json.dumps( data, separators=(',', ':')))  ## remove space else plugin will not match str

        except asyncio.CancelledError:  #raised when asyncio receives SIGINT from KB_Interrupt
            print(f"asyncio tasks: send stop signal, wait for exit...")
            self.stop_threads = True
            #try:
            #    await asyncio.get_running_loop().shutdown_asyncgens()
            #except RuntimeError: pass
            try:
                await asyncio.sleep( 3 )                          # these are not graceful exits.
                await asyncio.get_running_loop().stop()           # unrecco = asyncio.get_event_loop().stop()
            except: pass


    async def start_ws_server( self,aport ):
        print( f"Started RTD server: port={aport}, tf={self.timeframe}min, sym_count={self.ticker_count}, increment_sym={self.inc_sym}")
        async with websockets.serve(self.handler, "localhost", aport ):
            await self.broadcast_messages_count()


        return

    async def load_exchanges(self):
        tasks = [exchange.load_markets() for exchange in self.exchange_instances.values()]
        await asyncio.gather(*tasks)  # Run all load_markets() calls concurrently

    async def close_exchanges(self):
        tasks = [exchange.close() for exchange in self.exchange_instances.values()]
        await asyncio.gather(*tasks)  # Run all load_markets() calls concurrently

    async def fetch_market_watchlists(self, name, exchange):
        print(f"Fetching market data for {name}...")
        try:
            watchlist = os.path.join(self.watchlists_path, name + self.watchlist_suffix)
            market = await exchange.fetch_markets()
            df = pd.DataFrame(market)
            df_active = df[
                (df['active']==True) &
                (df['type'] == "spot")
            ]
            df_symlist = df_active['symbol'] + f"{name}"
            for i in range(len(df_symlist)):
                sym = df_symlist.iloc[0][i]
                self.add_symbol_from_df()
            print(df_symlist.to_string())
            df_symlist.to_csv(watchlist,index = False, header=None, mode = "w")
            await exchange.close()
        except Exception as e:
            print(f"Error fetching data for {name}: {e}")

    async def create_watchlists(self):
        tasks = [self.fetch_market_watchlists(name, exchange) for name, exchange in self.exchange_instances.items()]
        await asyncio.gather(*tasks)

    async def get_historic_data(self, json_message):
        #Todo logic to handle parsing of crypto vs non crypt data
        # Do soemthing like if not somesubstring found in exchangeList continue, etc
        if ' ' not in json_message['arg']:
            symbol_and_exchange = json_message['arg']
        else:
            argument = json_message['arg']
            symbol_and_exchange = argument.split(' ')[1]

        for exchange_name in self.exchange_instances.keys():
            if not exchange_name in symbol_and_exchange:
                continue
            else:
                exchange = self.exchange_instances[exchange_name.lower()]
                symbol = symbol_and_exchange.split(exchange_name)[0]
                break
        try:
            data = await exchange.fetch_ohlcv(
                                                symbol=symbol,
                                                timeframe = "1m"
                                                )
            formatted_data = [
                [
                    int((datetime.datetime.utcfromtimestamp(row[0] // 1000)
                         .replace(tzinfo=pytz.utc)  # Set timezone to UTC
                         .astimezone(self.timezone)  # Convert to Perth time
                         .strftime("%Y%m%d"))),  # Date as integer (YYYYMMDD)

                    int(datetime.datetime.utcfromtimestamp(row[0] // 1000)
                        .replace(tzinfo=pytz.utc)  # Set timezone to UTC
                        .astimezone(self.timezone)  # Convert to Perth time
                        .strftime("%H%M%S")),  # Time as integer (HHMMSS)

                    *row[1:],  # OHLCV values
                    0  # Extra 0 at the end
                ]
                for row in data
            ]
            json_dict = {"hist":f"{symbol_and_exchange}","format":"dtohlcvi"}
            json_dict['bars'] = formatted_data
            json_string = json.dumps(json_dict)
            await self.broadcast(json_string)


        except Exception as e:
            print(e)



async def main():
    print("Creating server")
    server = RTDServer()
    print("Loading exchanges")
    await server.load_exchanges()
    print("Exchanges loaded")
    await asyncio.gather(server.start_ws_server(server.websocket_port))
    await server.close_exchanges()

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