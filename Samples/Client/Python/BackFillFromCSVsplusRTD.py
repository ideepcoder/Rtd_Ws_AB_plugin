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

#For historic data, see what happens when assining to hd_str in some_historic_data
#For RTD data. Look at random_generator and decipher the variable assugnments there.

import asyncio
import aiofiles
from io import StringIO
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



logging.basicConfig(level=logging.DEBUG, filename="logs.txt", filemode="w")

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
    def __init__(self,
                 exchange = None
                 ):
        super().__init__()

        try:
            sleep_time = float(sys.argv[1])
            print(f'Frequency={sleep_time} secs')
        except:
            sleep_time = 0.9
            print(f'Frequency={sleep_time} secs')

        ''' Settings '''
        self.timeframe       = 5            ## base time interval in min (periodicity)
        self.websocket_port  = 10102        ## Websocket port  10102
        self.sleep_time      = sleep_time   ## simulate ticks generated every "n" seconds. SET IN MAIN()
        self.ticker_count    = 0            ## incl default 3 tickers, increase max_tickers accordingly
        self.inc_sym          = 1           ## set greater than 0, to simulate new quotes by this amount. IF 0, no new tickers added
        self.max_tickers        = 1000      ## maximum concurrent ticks Try 1000 :) no problem

        self.keep_running     = True   ## True=Server remains running on client disconnect, False=Server stops on client disconnect

        self.websocket_subscription_list = []        ## simulate add and remove symbol command
        self.data_list = []
        self.queue = asyncio.Queue()

        self.timezone = pytz.timezone('Australia/Perth')

        self.amibroker_path = "C:\\Program Files\\AmiBroker\\"
        self.databases_path = os.path.join(self.amibroker_path,"Databases")
        self.database = "CryptoLive" #Name database you will use for RTD data here
        self.DataFiles_dir = os.path.join(self.amibroker_path,"DataFiles")

        self.watchlists_path = os.path.join(self.databases_path,self.database,"WatchLists")
        self.watchlist_suffix = ".tls"
        self.watchlist = []

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
                    await websocket.send(message)         ## send broadcast RTD messages

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

    async def subscribe_to_exchange_websocket(self, symbol_and_exchange):
        print(f"Determining symbol and exchange: {symbol_and_exchange}")
        try:
            symbol_and_exchange = symbol_and_exchange.split()
            if len(symbol_and_exchange) > 1:
                symbol_and_exchange = symbol_and_exchange[1]
            else:
                symbol_and_exchange = symbol_and_exchange[0]
        except: pass
        print(f"Parsed value: {symbol_and_exchange}")
        symbol = None
        exchange = None
        for exchange_name in self.exchange_instances.keys():
            if not exchange_name in symbol_and_exchange:
                continue
            else:
                exchange = self.exchange_instances[exchange_name.lower()]
                symbol = symbol_and_exchange.split(exchange_name)[0]
                break
        print(f"Subscribing to websocket for {symbol_and_exchange}. Symbol:{symbol}\tExchange: {exchange}")
        current_candle = asyncio.create_task(exchange.fetch_ohlcv(symbol=symbol, timeframe="1m", limit=1))
        current_ticker_vals = asyncio.create_task(exchange.fetch_ticker(symbol=symbol))

        # Wait for both tasks to complete and get the results
        candle_data, ticker_data = await asyncio.gather(current_candle, current_ticker_vals)
        open_price = candle_data[0][1]
        high_price = candle_data[0][2]
        low_price = candle_data[0][3]
        volume = candle_data[0][5]
        prior_cumulative_volume = ticker_data['baseVolume']
        last_minute = datetime.datetime.utcnow().minute
        while True:
            data = await exchange.watch_ticker(symbol=symbol)
            await asyncio.sleep(0.03)
            timestamp = data['timestamp']
            date_string = datetime.datetime.fromtimestamp(timestamp / 1000).strftime("%Y%m%d")
            time_string = datetime.datetime.fromtimestamp(timestamp / 1000).strftime("%H%M%S")
            date_int = int(date_string)
            time_int = int(time_string)
            dt_object = datetime.datetime.utcfromtimestamp(timestamp / 1000)
            current_minute = dt_object.minute

            last_price = data['last']
            daily_vol = data['baseVolume']
            current_increment = abs(daily_vol - prior_cumulative_volume)
            prior_cumulative_volume = daily_vol
            volume += current_increment
            if current_minute != last_minute:
                last_minute = current_minute  # Update minute tracker
                volume = current_increment
                open_price = high_price = low_price = last_price

            volume = round(volume, 5)
            high_price = max(high_price, last_price)
            low_price = min(low_price, last_price)

            bid_price = data['bid']
            ask_price = data['ask']
            bid_volume = data['bidVolume']
            ask_volume = data['askVolume']
            open_price = open_price
            high_price = high_price
            low_price = low_price
            day_high = data['high']
            day_low = data['low']
            day_open = data['open']
            prev_close = data['previousClose']

            rtd = {
                "n": symbol_and_exchange,
                "t": time_int,
                "d": date_int,
                "c": last_price,
                "o": open_price,
                "h": high_price,
                "l": low_price,
                "v": volume,
                "oi": 0,
                "bp": bid_price,
                "ap": ask_price,
                "s": daily_vol,
                "bs": bid_volume,
                "as": ask_volume,
                "pc": prev_close,
                "do": day_open,
                "dh": day_high,
                "dl": day_low
            }
            self.data_list.append(rtd)


    async def unsubscribe_from_exchange_websocket(self,symbol_and_exchange):
        print(f"Determining symbol and exchange to unsubscribe: {symbol_and_exchange}")
        try:
            symbol_and_exchange = symbol_and_exchange.split()
            if len(symbol_and_exchange) > 1:
                symbol_and_exchange = symbol_and_exchange[1]
            else:
                symbol_and_exchange = symbol_and_exchange[0]
        except:
            pass
        print(f"Parsed value: {symbol_and_exchange}")
        try:
            symbol = None
            exchange = None
            for exchange_name in self.exchange_instances.keys():
                if not exchange_name in symbol_and_exchange:
                    continue
                else:
                    exchange = self.exchange_instances[exchange_name.lower()]
                    symbol = symbol_and_exchange.split(exchange_name)[0]
                    break
            print(f"Unsubscribing to websocket for {symbol_and_exchange}. Symbol:{symbol}\tExchange: {exchange}")
            await exchange.un_watch_ticker(symbol)
        except Exception as e:
            print(f"Exception: {e}")

    async def recv(self, websocket ):
                try:
                    while( not self.stop_threads ):
                        try:
                            async with asyncio.timeout(20):
                                message = await websocket.recv()
                                print(message)
                                try:
                                    json_message = json.loads( message )
                                    print(json_message)
                                    if 'cmd' in json_message:
                                        if "bfsym" in json_message['cmd']:
                                            if "arg" in json_message:
                                                if ' ' in json_message['arg']:
                                                    try:
                                                        command = json_message['arg'].split()
                                                        try:
                                                            backfill_length = int(command[2])
                                                            if backfill_length == 1:
                                                                asyncio.create_task(
                                                                    self.get_historic_data(json_message)
                                                                )
                                                                self.add_symbol(json_message)
                                                            elif backfill_length == 5:
                                                                symbol_and_exchange = command[1]
                                                                asyncio.create_task(self.exchange_data_from_file_backfill_crypto(symbol_and_exchange))
                                                                self.add_symbol(json_message)
                                                        except Exception as e:
                                                            print(f"Exception: {e}")

                                                    except Exception as e:
                                                        print(f"Exception: {e}")

                                        elif "bfall" in json_message['cmd']:
                                            if "arg" in json_message:
                                                if json_message['arg']=='x':
                                                    pass #todo handle this

                                        elif "bffull" in json_message['cmd']:
                                            symbol_and_exchange = (json_message['arg'])
                                            asyncio.create_task(
                                                self.exchange_data_from_file_backfill_crypto(symbol_and_exchange)
                                            )


                                        elif "bfauto" in json_message['cmd']:
                                            #todo implement properly
                                            print("Backfilling data since last data point for 1 symbol."
                                                  "For now just use the csv and most recent call"
                                                  "We will implement later."
                                                  )
                                            symbol_and_exchange = (json_message['arg'])
                                            asyncio.create_task(
                                                self.exchange_data_from_file_backfill_crypto(symbol_and_exchange)
                                            )

                                        elif "addsym" in json_message['cmd']:
                                            print("Subscribing to websocket")
                                            asyncio.create_task(
                                                self.subscribe_to_exchange_websocket(json_message['arg'])
                                            )

                                        elif "remsym" in json_message['cmd']:
                                            print ("Unsubscribing from websocket")
                                            asyncio.create_task(
                                                self.unsubscribe_from_exchange_websocket(json_message['arg'])
                                            )

                                        else:
                                            print("Unknown command in message")

                                    else:
                                        print( f"json_message={message}")

                                    await asyncio.sleep(self.sleep_time)

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

    def add_symbol(self, json_message):
        try:
            json_copy = copy.deepcopy(json_message)
            sym = json_copy['arg']
            print(f"Adding symbol ")
            if sym not in self.websocket_subscription_list:
                self.websocket_subscription_list.append(sym)
                symbol_and_exchange = sym
                asyncio.create_task(self.subscribe_to_exchange_websocket(symbol_and_exchange))
                json_copy['code'] = 200
                json_copy['arg']  = sym + " subscribed ok"
            else:
                json_copy['code'] = 400
                json_copy['arg']  = sym + " already subcribed"
            print(json.dumps(json_copy, separators=(',', ':')))
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
            symbol_and_exchange = sym
            asyncio.create_task(self.unsubscribe_from_exchange_websocket(symbol_and_exchange))
            json_copy['code'] = 200
            json_copy['arg']  = sym + " unsubcribed ok"

        return json.dumps( json_copy, separators=(',', ':') )

    def broadcast(self, message ):
        print(message)
        self.publish(message)

    def random_generator(self, l=1, u=9): return random.randint(l, u)

    async def pull_data_from_exchange_websockets(self):
        try:
            while not self.stop_threads:
                data = self.data_list
                self.data_list = []
                data_for_broadcast = json.dumps(data, separators=(',', ':'))
                await self.queue.put(data_for_broadcast)
                await asyncio.sleep(self.sleep_time)
        except asyncio.CancelledError:  #raised when asyncio receives SIGINT from KB_Interrupt
            print(f"asyncio tasks from exchange websocket: send stop signal, wait for exit...")
            self.stop_threads = True
            try:
                await asyncio.sleep( 3 )                          # these are not graceful exits.
                await asyncio.get_running_loop().stop()           # unrecco = asyncio.get_event_loop().stop()
            except: pass

    async def broadcast_messages_count(self):
        asyncio.create_task(self.pull_data_from_exchange_websockets())
        try:
            while not self.stop_threads:
                data = await self.queue.get()
                self.broadcast(data)
                await asyncio.sleep(self.sleep_time)    #simulate ticks in seconds

        except asyncio.CancelledError:  #raised when asyncio receives SIGINT from KB_Interrupt
            print(f"asyncio tasks: send stop signal, wait for exit...")
            self.stop_threads = True
            try:
                await asyncio.sleep( 3 )                          # these are not graceful exits.
                await asyncio.get_running_loop().stop()           # unrecco = asyncio.get_event_loop().stop()
            except: pass

    async def start_ws_server( self,aport ):
        print( f"Started RTD server: port={aport}\ntimeframe={self.timeframe}min\nsym_count={self.ticker_count}\nincrement_sym={self.inc_sym}")
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
        #todo implement properly watchlists
        try:
            watchlist = os.path.join(self.watchlists_path, name + self.watchlist_suffix)
            market = await exchange.fetch_markets()
            df = pd.DataFrame(market)
            df_active = df[
                (df['active']==True) &
                (df['type'] == "spot")
            ]
            df_symlist = (df_active['symbol']).upper().replace("/","-") + f".{name.lower()}"
            print(df_symlist.to_string())
            df_symlist.to_csv(watchlist,index = False, header=None, mode = "w")
            await exchange.close()
        except Exception as e:
            print(f"Error fetching data for {name}: {e}")

    async def create_watchlists(self):
        tasks = [self.fetch_market_watchlists(name, exchange) for name, exchange in self.exchange_instances.items()]
        await asyncio.gather(*tasks)

    async def get_historic_data(self, json_message):
        print(f"Fetching Data. Extracting symbol from message:{json_message}")
        if ' ' not in json_message['arg']:
            symbol_and_exchange = json_message['arg']
        else:
            argument = json_message['arg']
            symbol_and_exchange = argument.split(' ')[1]
        print(f"Fetching Data for {symbol_and_exchange}")
        exchange = None
        symbol = None
        for exchange_name in self.exchange_instances.keys():
            if not exchange_name in symbol_and_exchange:
                continue
            else:
                exchange = self.exchange_instances[exchange_name.lower()]
                symbol = symbol_and_exchange.split(".")[0]
                break
        print("Making exchange data call from get_historic_data")
        asyncio.create_task(self.exchange_data_call(symbol_and_exchange,exchange,symbol,self.timeframe))

    async def exchange_data_call(self, symbol_and_exchange, exchange, symbol, timeframe):
        try:
            symbol = symbol.replace("-", "/")
            print(f"Calling {timeframe} data for {symbol} from {exchange}")
            exchange = ccxtpro.binance()
            data = await exchange.fetch_ohlcv(
                                                symbol=symbol,
                                                timeframe =f"{timeframe}m",
                                                limit = 1000
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
            await self.queue.put(json_string)

        except Exception as e:
            print(e)


    async def exchange_data_call_return(self, exchange, symbol, timeframe):
        try:
            print(f"Calling {timeframe} data for {symbol} from {exchange}")
            symbol = symbol.replace("-", "/")
            data = await exchange.fetch_ohlcv(
                                                symbol=symbol,
                                                timeframe = f"{timeframe}m",
                                                limit = 1000
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
            return formatted_data

        except Exception as e:
            print(e)
            return []

    async def exchange_data_from_file_backfill_crypto(self, symbol_and_exchange):
        try:
            print(f"Fetching Data for {symbol_and_exchange} from backfill file")
            exchange = None
            symbol = None
            for exchange_name in self.exchange_instances.keys():
                if not exchange_name in symbol_and_exchange:
                    continue
                else:
                    exchange = self.exchange_instances[exchange_name.lower()]

                    #Modify next statement depending on how you stored the name of the symbol.
                    # CCXT prefers BTC/USDT etc
                    symbol = symbol_and_exchange.split(".")[0].upper()
                    break


            symbol = symbol.replace("-","")
            symbol = symbol.replace("/", "")
            full_path = os.path.join(self.DataFiles_dir,f"{symbol}.csv")
            async with aiofiles.open(full_path,mode="r") as f:
                file_content = await f.read()

            df = pd.read_csv(StringIO(file_content), header=None)
            df[1] = df[1].astype(str).str.replace("-", "").astype(int)  # YYYYMMDD
            df[2] = df[2].astype(str).str.replace(":", "").astype(int)  # HHMMSS
            df = df[[1, 2, 3, 4, 5, 6, 7]]
            bars = [
                [int(row[0]), int(row[1]), row[2], row[3], row[4], row[5], row[6], 0]
                for row in df.itertuples(index=False, name=None)
            ]

            latest_bars = await (self.exchange_data_call_return(exchange, symbol, self.timeframe))
            bars.extend(latest_bars)
            json_data = {
                "hist": symbol_and_exchange,
                "format": "dtohlcvi",
                "bars": bars
            }
            json_string = json.dumps(json_data)
            await self.queue.put(json_string)

        except Exception as e:
            print(f"Exception getting data from csv: {e}")

async def main():
    try:
        print("Creating server")
        server = RTDServer()
        print("Loading exchanges")
        await server.load_exchanges()
        print("Exchanges loaded")
        await asyncio.gather(server.start_ws_server(server.websocket_port))
        await server.close_exchanges()
        print("Exit 0")
    except KeyboardInterrupt:
        server.stop_threads = True
        await server.close_exchanges()
        print(f"Kill signal, Exit 1")
    except asyncio.CancelledError:
        pass
    except Exception:
        pass

if __name__ == "__main__":
    asyncio.run(main())
