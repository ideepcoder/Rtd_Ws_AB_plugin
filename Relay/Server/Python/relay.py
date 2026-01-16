'''
//      #####   Relay_Server.py   #####
//
// Independent Relay server for WsRtd AmiBroker Data Plugin
//
// Central Websocket Python Program that runs as a Server.
// Both, CLient Application RTD Senders and the WsRTD data plugin
// connect to this server via specified IP:Port
//
// The advantage is that either Sender-Client or Receiver-client
// can restart or drop the connection without affecting the other.
// In the future, it will also serve to hook ArcticDB integration into the system.
//
///////////////////////////////////////////////////////////////////////
// Author: ideepcoder
// https://github.com/ideepcoder/Rtd_Ws_AB_plugin/
// https://forum.amibroker.com/u/nsm51/summary
//
// Users and possessors of this source code are hereby granted a nonexclusive, 
// royalty-free copyright license to use this code in individual and commercial software.
//
// AUTHOR ( ideepcoder ) MAKES NO REPRESENTATION ABOUT THE SUITABILITY OF THIS SOURCE CODE FOR ANY PURPOSE. 
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


## stable with ws-close(), handles with BaseException catch. Just prints the exception though.
## use as middle server to recv from one client and send to another.
## this is working code with ctrl+c issue fixed
wsport = 10101

import asyncio
import websockets
import threading
import datetime
import sys

## Globals ##
stop_event   = 0
stop_threads = False
CLIENTS      = set()
SENDERS      = set()
ctr          = [0, 0, 0, 0]    # counters: clients, senders, reserved
retCode      = 0


'''Experimental Code for Trading Interface'''
'''It is better to run TI on a separate port'''
BROK_CLIENT = set()
BROK_WS     = set()

'''
Function to iterate over all CLIENTS and broadcast message received from SENDER
'''
async def broadcast_c( message ):
    global CLIENTS

    Bad_WS = set()

    for websocket in CLIENTS:
        try:
            await websocket.send( message )

        except websockets.ConnectionClosed:                        Bad_WS.add( websocket ); continue
        except ConnectionResetError:                               Bad_WS.add( websocket ); continue
        except Exception as e: print(f"broadcast_C() {e}");        break
    
    if len( Bad_WS ) > 0:
        for ws in Bad_WS:
            CLIENTS.remove( ws )

    if len( CLIENTS ) < 1:  await broadcast_s( "NO_ACTIVE_CLIENTS" ); print("NO_ACTIVE_CLIENTS")


'''
Function to iterate over all SENDER(S) and broadcast message received from CLIENTS
'''
async def broadcast_s( message ):
    global SENDERS
    
    Bad_WS = set()

    for websocket in SENDERS:
        try:
            await websocket.send( message )
        except websockets.ConnectionClosed:                        Bad_WS.add( websocket ); continue
        except ConnectionResetError:                               Bad_WS.add( websocket ); continue
        except Exception as e: print(f"broadcast_S() {e}");        break

    
    if len( Bad_WS ) > 0:
        for ws in Bad_WS:
            SENDERS.remove( ws )
        
    if len( SENDERS ) < 1:  print("NO_ACTIVE_SENDERS")



'''
Main function that creates Handler for Each websocket connection (ie. Send() / Receive() functionality)
'''
async def handler( websocket ):
    global stop_event, stop_threads, SENDERS, CLIENTS, ctr
    role = l_role = 0      ## local role

    try:
        role = await websocket.recv()

        if str(role).startswith('role'):
            if str(role).endswith('send'):  SENDERS.add( websocket); l_role = 1
            else:                           CLIENTS.add( websocket); l_role = 2

        elif str(role).startswith('broker'):
            if str(role).endswith('ws'):    BROK_WS.add( websocket);     l_role = 3
            else:                           BROK_CLIENT.add( websocket); l_role = 4

    except: pass

    ## create periodic task:    ## disabled task to work as echo server. Client (fws) -> WS_server->Client C++
    #asyncio.create_task(send(websocket))
    try:
        if   l_role==1:
            print(f"sender conn"); ctr[1]+=1; await stats(); await asyncio.create_task( senders_t( websocket))
            print(f"sender disc"); ctr[1]-=1
        elif l_role==2:
            print(f"client conn"); ctr[0]+=1; await stats(); await asyncio.create_task( clients_t( websocket))
            print(f"client disc"); ctr[0]-=1
        else:   print(f"Bad Auth: {role}"); await websocket.send('Server: Bad or No Auth')

    except TimeoutError:                                pass
    except websockets.ConnectionClosed:                 return
    except ConnectionResetError:                        return
    except Exception as e:print(f"handle() Ex {e}");    return
    except BaseException as e:print(f"handle() BEx {e}");return



'''
Individual Role-Senders RECEIVE function as task, this message is BROADCAST to all CLIENTS
'''
async def senders_t( websocket ):
    global stop_threads, stop_event
    while not stop_threads:
        try:
            # this code is for normal recv but now above is just echo            
            message = await websocket.recv()
            #print(message)
            await broadcast_c( message)

        except TimeoutError:                pass
        except websockets.ConnectionClosed: break                 ## connection drops
        except ConnectionResetError:                        break
        except Exception as e:print(f"senders() Ex {e}");   break
    return 0



'''
Individual Role-Clients RECEIVE function as task, this message is BROADCAST to all SENDERS
'''
async def clients_t( websocket ):
    global stop_threads, stop_event
    while not stop_threads:
        try:
            # this code is for normal recv, can use async as well for timeout           
            message = await websocket.recv()
            print(message)                          # print client msessages in server
            await cmdMmessage( message )

        except TimeoutError:                                pass
        except websockets.ConnectionClosed:                 break
        except ConnectionResetError:                        break
        except Exception as e:print(f"clients() Ex {e}");   break
    return 0



'''
utility function to parse CLIENTS commands / testing
'''
async def cmdMmessage( message ):
    global stop_threads, stop_event
    try:
        if message == "zzz":            ## just testing
            print(f"kill sig rec'd");   stop_threads = True
            await asyncio.sleep(1);     stop_event.set()
        elif message == "close":
            print(f"recd shutdown from client")
        else:
            await broadcast_s( message )
    except: pass
    return 0



'''
utility function to print counts of Role-Senders & Role-Clients
'''
async def stats():
    global ctr
    print(f"Clients={ctr[0]}, Senders={ctr[1]}")



'''
Websocket Server init.
'''
async def ws_start( stop ):
    global stop_event, wsport, retCode
    print(f"RTD Relay server started: {datetime.datetime.now()} on localhost:{wsport},\nctrl+c once to shutdown.")
    try:        
        async with websockets.serve(handler, "localhost", wsport):
            await stop
            
    except Exception as e:    print(f"ws_start() Ex {e}");  stop_event.set(); retCode = 404;  return


'''
Main function to create Asyncio Event_Loop and start Websocket Server.
'''
def main_S( lst=[] ):
    global stop_event, stop_threads, wsport, retCode

    try:
        if len( lst ) > 2:                          ## sys.argv[0] = dummy
            p = int( lst[1] )                       ## try to int
            if lst[2] == "startserver":
                wsport = p
            else: print(f"Bad args"); exit(404)

    except: print(f"first arg is port#"); exit(404)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop( loop )
        stop_event = threading.Event()
        stop = loop.run_in_executor(None, stop_event.wait)

        loop.run_until_complete( ws_start( stop ))
        stop_threads = True; loop.stop(); loop.close()

    except Exception as e: print(f"main() Ex {e}"); stop_threads = True; stop_event.set(); loop.stop()
    except BaseException as b:print(f"main() bEx {b}"); stop_threads = True; stop_event.set(); loop.stop()
    print(f"shutdown server. Exit {retCode}");  exit( retCode)



if __name__ == "__main__":
    if( len( sys.argv) > 2):    main_S( sys.argv )  ## default port 10101
    else:                       main_S( ['main', str(wsport), 'startserver' ]  )


## Credits:
## ideepcoder, Author.