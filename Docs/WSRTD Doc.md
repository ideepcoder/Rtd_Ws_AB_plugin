# WS_RTD_AB
## _AmiBroker Realtime data plugin using Websocket and JSON based communication_

[![Build Status](https://raw.githubusercontent.com/ideepcoder/Rtd_Ws_AB_plugin/84c47468847d2bbf53d2f12fa110d13c041d7b2d/images/unknown.svg)](https://github.com/ideepcoder/Rtd_Ws_AB_plugin)
Doc version: 1.2, Plugin: 3.03.16
## Features
- Bi-directional websocket communication
- Support to backfill historical data
- Easy to integrate Json message structure
- Run multiple instances of AmiBroker locally, each connected to one of multiple Servers
- The design makes it Broker / Data vendor agnostic
- Runs a python based relay server, to ensure individual connections don't disrupt your flow
- Build your own data routing logic
- Store your time-series data in the superfast Amibroker storage database
- Get you Realtime Quote window ticking as opposed to plain ASCII imports
- Supports updating Symbol Information, Extra Data and Fundamental data 

# ✨ Upcoming  ✨
- ArcticDB active integration
- A lot of leverage with keeping bloated data locally in ArcticDB and a concise Amibroker database


### To-do: Table of Contents and Anchor links


##### For DLL/Binary redistribution, kindly read the LICENSE section.
============================================

## Installation

WS_RTD requires [AmiBroker] to run.
| Software | Supported / Tested version |
| ------ | ------ |
| AmiBroker | v6.30+ x64-bit |
| Visual C++ | VC++ 2022 redistributable |
| Windows OS | Windows 10/11 x64-bit|
| Linux OS| To-Do|
|  Vanilla Python | [3,12 x64-bit](https://www.python.org/downloads/release/python-3120/) or higher|
Install the above dependencies.
Sample codes like sample_server.py requires additional python packages to be installed.

##### The plugin 
```sh
Copy WsRTD.dll to C:\PATH\AmiBroker\Plugins folder
```

##### Run Amibroker and Create New Database
https://www.amibroker.com/guide/w_dbsettings.html
```sh
File > New > Database
```

##### Configure the Database
```sh
select Database folder
Datasource: WsRtd data Plug-in
Local data storage: ENABLE  (very important)
set: Number of bars
Base time interval: 1 minute or as suited
```
*To-Do: Enabling seconds(timeframe) in next iteration. Tick-data unsupported for now*

[![img create](https://github.com/ideepcoder/Rtd_Ws_AB_plugin/blob/main/images/help/DB_Create.png?raw=true)]

##### Configure the Plug-in
```sh
Click Configure button
```

[![img configure](https://github.com/ideepcoder/Rtd_Ws_AB_plugin/blob/main/images/help/Plugin_Configure.png?raw=true)]

The internal plug-in DB stores RTD Quotes as a RING BUFFER. Max_Num_Sym_Quotes here means the number of bars to hold. If you run Analysis frequently and ensure all symbols are accessed, then you can set it as low as 10 to reduce memory usage. Each bar is 40 KB.

#### Important Settings change:
1. **Max_Num_SYM_Quotes** : Requires AB restart
2. ***Changes in IP / Port / AUTH** : Requires Plugin shutdown / connect, ie. Reconnect. 

##### The Sample Server
ensure these Python packages are installed and their dependencies
```sh
import asyncio
import websockets
import datetime
import json
import random
import sys
import pandas as pd
import copy
```
start the sample server in a Windows terminal,
```sh
cd \path\to\server
py sample_Server.py
```
[![img sample_server1](https://github.com/ideepcoder/Rtd_Ws_AB_plugin/blob/main/images/help/sample_s1.png?raw=true)]

[![img sample_server1](https://github.com/ideepcoder/Rtd_Ws_AB_plugin/blob/main/images/help/sample_s2.png?raw=true)]

**When Data Plug-in connects to the server**

[![img baloon1](https://github.com/ideepcoder/Rtd_Ws_AB_plugin/blob/main/images/help/Plugin_baloon_OK.png?raw=true)


# JSON FORMATS
There are 4 types: Json-RTD, Json-HIST, Json-CMD, Json-ACK

### 1) RTD format in json message
Currently, minimum periodicty/timeframe/interval of bars is 1 minute.
Valid fields in the json object
**ORDER** See the Json recommended section, rtd message has to start with "n" field. Subsequent order does not matter.
**STRUCTURE** This is Array of JSON strings

>'n', 'd', 't', 'o', 'h', 'l', 'c', 'v', 'oi', 'x1', 'x2', ( for Quotations )
's','pc','bs','bp','as','ap', 'do', 'dh', 'dl' ( for Realtime Quote window)

> 'n'=symbol name, date, time, open, high, low, close, volume, open interest,
>'x1'=Aux1, 'x2'=Aux2
's'=total daily vol, 'pc'=prev day close, 
'do', 'dh', 'dl', are Day Open, High, Low
'bs', 'bp', 'as', 'ap', are bid size/ bid price /ask size / ask price 

>Sample rtd json
```sh
[{"n":"SYM1","t":101500,"d":20241130,"c":3,"o":6,"h":9,"l":1,"v":256,"oi":0,"bp":4,"ap":5,"s":12045,"bs":1,"as":1,"pc":3,"do":3,"dh":9,"dl":1},{"n":"SYM2","t":101500,"d":20241130,"c":3,"o":6,"h":9,"l":1,"v":256,"oi":0,"bp":4,"ap":5,"s":12045,"bs":1,"as":1,"pc":3,"do":3,"dh":9,"dl":1},{"n":"SYM3","t":101500,"d":20241130,"c":3,"o":6,"h":9,"l":1,"v":256,"oi":0,"bp":4,"ap":5,"s":12045,"bs":1,"as":1,"pc":3,"do":3,"dh":9,"dl":1}]
```
Supported Date/Time formats:
```sh
milliseconds not yet supprted
u = unix timestamp localtime()   ( type: integer64 )
g = unix timestamp gmtime()      ( type: integer64 )
d = date                         ( type: integer )
t = time                         ( type: integer )
u, g and d are MUTUALLY EXCLUSIVE, but any one is mandatory.
"t" is mandatory for RTD along with "d"
/U=unix_local_ms /G=unix_utc_ms (To-Do:)
```

Refer to Amibroker ADK link above for data types.
'd'.'t','as','bs' as integer,
float is safe for the rest.
To-do: unix timestamp(u/g), seconds interval

if required fields are not found, they are set to ZERO & that will distort candles.
```sh
o, h, l, c = open,high,low,last_traded_price = mandatory for new Quote
v, oi, x1, x2 = optional and set to 0 if absent

Realtime Quote window variables are optional, but they
are required for this feature to work properly.
```
Using d,t is more efficient over u,g as 1 step less in conversion and should be preferred if available.

### 2) History format in json message
Parse a history data JSON string that is used to backfill a Ticker

>This is all the backfill records in Array format for a single ticker
format specifier is fieldsStr = "dtohlcvixy"
only valid fields should be set and in that particular order.

 **ORDER** The sequence of columns in hostorical data can be anything set by the user, but it has to match its character in the Format specifier string. The beginning of the json message will start with "hist" containing Symbol name followed by "format" field containing the Format specifier string.
 
 **Important: History Array records must be in ascending order**, ie. Least DateTime first.
```sh
(ugdt)ohlcvixy
milliseconds not yet supprted
u = unix timestamp localtime()   ( type: integer64 )
g = unix timestamp gmtime()      ( type: integer64 )
d = date                         ( type: integer )
t = time                         ( type: integer )
u, g and d are MUTUALLY EXCLUSIVE, but any one is mandatory.
"t" is mandatory for intraday bars with "d"

o = open price        ( type: float ), required
h = high price        ( type: float ), required
l = low price         ( type: float ), required
c = close price       ( type: float ), required
v = volume            ( type: float ), optional
i = open interest     ( type: float ), optional
x = aux1              ( type: float ), optional
y = aux2              ( type: float ), optional
/U=unix_local_ms /G=unix_utc_ms (To-Do:) 
```
if required fields are not found, they are set to ZERO & that will distort candles.

##### bars field is JSON Value Array
>Sample Date-Time
>DATE (optional TIME) d,t is supplied as INT,
```sh
{"hist":"SYM1","format":"dtohlcvi","bars":[[20240601,100000,22.1,22.5,22.1,22.8,120,0],
[20240602,110000,22.8,22.7,22.3,22.4,180,0],[20240603,120000,22.8,22.7,22.3,22.4,180,0]]}
```

>Sample unix timestamp
```sh
({"hist":"SYM1","format":"uohlcv","bars":[[1731670819,22.1,22.5,22.1,22.8,120],
[1731761419,22.8,22.7,22.3,22.4,180]]}
```
>u=Unix Local timestamp	OR g=Unix GMT/UTC timestamp
that is use ( windows struct tm = localtime() or tm = gmtime()

 
##### Backfill style-01
>Currently, Vendor backfill means N most recent days data
so plugin also sets Bars from the first of this Array to the last bar
the existing bars are overwritten, from first bar of hist.
old_data + WS_data
Now, backfill means old_data + backfill (upto last backfill)
then, old_data + backfill_data + Rt_data ( from bars after last backfill bar, if any )

[![img sample_server1](https://github.com/ideepcoder/Rtd_Ws_AB_plugin/blob/main/images/help/Plugin_menu.png?raw=true)

##### Backfill style-02 *To-do:*
Inserting historical data into AmiBroker Database 

### 3) CMD format in json message
Work in progress, subject to change.
> ALL REQUESTS made by **plug-in TO** Server have only "cmd" and "arg fields"
> Server should REPLY to all above REQUESTS with same "cmd" and "arg" fields. Additionally inserting the "code" which is integer.
> Code values for OK=200 to 299, and OTHER/BAD=400 to 499. Specific codes are not defined yet.

> ALL REQUESTS made by **Server To** Plug-in will have valid "cmd" and "arg" fields. Additionally, all SERVER-side requests will have code=300 which is integer.
>( The only exceptions is json-RTD and json-HIST formats.)

> Plug-in will respond with **Acknowledgement TO Server** for all code=300 Server-side REQUESTS with json-ACK "ack" with server-request, "arg" with description and "code" which is integer
> Code values for OK=200 to 299, and OTHER/BAD=400 to 499. Specific codes are not interpreted currently.


#### 3.1) Request CMD from plugin to "Server"

##### a) First Access automatic symbol backfill request ( use as SUBSCRIBE signal )
This is a special automatic backfill request command that is sent to the server when a symbol is accessed in Amibroker for the first time. Server can choose to ignore this request or respond with a json-History backfill data of a desired period.
{"cmd":"bfauto","arg":"SYMBOL_NAME DateNum TimeNum"}  last Quote timestamp sent when symbol has some data
{"cmd":"bffull","arg":"SYMBOL_NAME"}  sent when symbol has NO data
```sh
{"cmd":"bfauto","arg":"SYM3 20241125 134500"}
{"cmd":"bffull","arg":"SYM9"}
```

##### b) single symbol backfill
{"cmd":"bfsym","arg":"reserved SYMBOL_NAME int_preset"}
```sh
{"cmd":"bfsym","arg":"y SYM1 3"}
```

##### c) ALL symbol backfill
{"cmd":"bfall","arg":"x"}
```sh
{"cmd":"bfall","arg":"x"}
```
For ALL Symbol backfill, client application should still send individual Json-hist messages for each symbol.

##### d) ADD symbol to SUBSCRIBE rtd
{"cmd":"addsym","arg":"SYMBOL_NAME"}
```sh
{"cmd":"addsym","arg":"SYM10"}
```

##### e) REMOVE symbol OR UNSUBSCRIBE rtd
{"cmd":"remsym","arg":"SYMBOL_NAME"}
```sh
{"cmd":"remsym","arg":"SYM6"}
```

##### f) CLIENT-APP connected request ping
{"cmd":"cping","arg":""}
```sh
{"cmd":"cping","arg":""}
```
Get state if any Client-App is connected to the relay. Also, a ping-alive packet that wsrtd is connected to Relay server.


##### g) Extra-Data request for Symbol
{"cmd":"ed","arg":"SYMBOL_NAME"}
```sh
{"cmd":"ed","arg":"SYM1"}
```
Extra-Data json has been requested for the particular Symbol by the Plugin.
User can return relevant json-ed. Look at Extra-Data Format for more information on allowed types.


#### 3.2) Response CMD "to WS_RTD" Plug-in from Server

##### a) General acknowledgement response
{"cmd":"CMD_SENT","code":int_code,"arg":"response string"}
Mandatory code field
```sh
{"cmd":"remsym","code":200,"arg":"SYM6 unsubscribed ok"}    /* sucess example*/
{"cmd":"addsym","code":400,"arg":"XYZ9 subscribe error, invalid"} /* failure example*/
```

##### b) Ping acknowledgement response
Mandatory code field
```sh
{"cmd":"cping","code":200,"arg":"Vendor Connected"}    /* Client running & connected to remote*/
{"cmd":"cping","code":400,"arg":"Vendor Disconnected"} /* Client running but remote source is disconnected*/
```


#### 3.3) Request CMD "to WS_RTD" Plug-in "from" Server
Mandatory code=300
{"cmd":"request_cmd","code":300,"arg":"request_arg"}

##### a) REMOVE or DELETE a Symbol "IN" plug-in Database
{"cmd":"dbremsym","code":300,"arg":"SYMBOL_NAME"}
Case-sensitive match
This is useful to FREE memory in the plug-in DB
```sh
{"cmd":"dbremsym","code":300,"arg":"SYM9"}
returns {"ack","code":200."arg":"SYM9 removed from DB"}     /* success */
returns {"ack","code":400,"arg":"SYM9 NOT found in DB")     /* failure */
```

##### b) Get the List of Symbols in Plug-in Database
{"cmd":"dbgetlist","code":300,"arg":""}
"arg" field required, can set empty or some string description
returns a comma-string of symbols
```sh
{"cmd":"dbgetlist","code":300,"arg":"DB Symbol list requested at 14:56:00"}
returns {"ack":"dbgetlist","code":200,"arg"="AA,AAPL,AXP,BA,C,CAT,IBM,INTC,"}
```

##### c) Get the Base Time Interval of Plug-in Database
{"cmd":"dbgetbase","code":300,"arg":""}
"arg" field required, can set empty
returns a STRING with base time interval in seconds(convert to INT)
```sh
{"cmd":"dbgetbase","code":300,"arg":"DB Symbol list requested at 14:56:00"}
returns {"ack":"dbgetbase","code":200,"arg"="60"}
```

##### d) Get the DB Status of Plug-in Database
{"cmd":"dbstatus","code":300,"arg":""}
"arg" field required, can set empty
returns a STRING with Format as ( convert to INT )
Current_Sym_Count, Max_Sym_Limit, Max_Size_Sym_Quotes, Refresh_Interval, Base_Interval, DB_Name
```sh
{"cmd":"dbstatus","code":300,"arg":"DB Status requested at 14:56:00"}
returns {"ack":"dbstatus","code":200,"arg"="500 1000 200 300 60 Db_Test"}
```


### 4) ACK format in json message
Plug-in will respond with **Acknowledgement TO Server** for all code=300 Server-side REQUESTS with json-ACK "ack" with server-request, "arg" with description and "code" which is integer
Code values for OK=200, and OTHER/BAD=400
```sh
For samples, check 3.3 Plug-in return messages
```


### 5) INFO format in json message
This is a special json packet to populate the Symbol Information data in AB.

*Note: Only some fields are implemented

**ORDER** See the Json recommended section, info message has to start with "info" field. Subsequent order does not matter.

**STRUCTURE** This is simple fields strings/int/float.

> Refer ADK Struct StockInfo, ALL ARE OPTIONAL. Use relevant fields only.

```sh
'an' = AliasName		( type: char ), MAX_LENGTH = 47 
'wi' = WebID			( type: char ), MAX_LENGTH = 47 
'fn' = FullName 		( type: char ), MAX_LENGTH = 127 
'ad' = Address	    	( type: char ), MAX_LENGTH = 127 
'co' = Country		    ( type: char ), MAX_LENGTH = 63
'cy' = Currency		    ( type: char ), ISO 3 letter currency code
'im' = MarketID 		( type: integer )
'ig' = GroupID		    ( type: integer )
'ii' = IndustryID		( type: integer )
'gc' = GICS			    ( type: integer ) 
```
>Sample info json
```sh
{"info":"SYM1","fn":"SYMBOL 1","an":"SYM1.NS","ad":"forum","co":"IN","cy":"INR","wi":"SYM1","im":0,"ig":0,"ig":0,"gc":0}
```


### 6) Extra Data format in json message
A very effective json format that allows CUSTOM USER-DEFINED "FIELDNAMES" that can be accessed by AFL in AB.
It implements the [GetExtraData("fieldname")](https://www.amibroker.com/guide/afl/getextradata.html) function in AB AFL, but allows more flexibilty based on the users need.
The Data is not persistent, will need to be sent again if AB is restarted.

**ORDER** See the Json recommended section, ExtraData message has to start with "ed" field. Subsequent order does not matter.

**STRUCTURE** This is simple fields string, float, Array of numbers.

> Refer AB manual, atleast one field is required.
```sh
The mapping is KEY:VALUE, and the same Case-sensitive Key should be called from AFL.
The Data Type are only those supported in AFL.

Arrays:
1. In the case of Array, the BarCount size in AFL is used, and most recent BarCount values are returned if there is an overflow.
2. Array values must be numeric, which can be cast to FLOAT, else they are converted to AFL NULL(-1e10f).
3. Timeframe is not adjusted, the Array elements will be populated consecutively in the Array-TimeFrame requested by AFL.
```
>Sample Extra Data json
```sh
{"ed":"SYM1","Beta":1.2,"IssueType":"EQ","MyCustomArr1":[11,10.00,-12,9.2,-5,0,2]}
```

Related commands or FieldNames used in AFL, via GetExtraData()
**CASE-SENSITIVE**
```sh
"ExtraDataStatus", "ExtraDataFields", "ExtraDataRequest", "CUSTOM_FIELDNAME"
```

1) ExtraDataStatus
Returns Count of FieldNames for current Symbol, else returns 0, if no fields exist.
One can use this to check before request json-ed command via ExtraDataRequest.

2) ExtraDataFields
Returns a comma-separated string containing valid/available "FieldNames" for the symbol, else returns 0.
It can be used in AFL to query valid FieldNames as each symbol supports custom extra data fields.

3) ExtraDataRequest
Sends a json-ed request with current symbol to the CLIENT-APP.
AFL can be used to request data when required.

4) CUSTOM_FIELDNAME
Pass the custom fieldname to access data and use in your AFL.
If FieldName is not found, -1 is returned (float).


### Important: Json string compression and format
* Json message should be compressed removing all whitespaces or prettify.
* Use your library Json Encoder to prevent errors.
For example, *The JSON standard requires double quotes and will not accept single quotes*
* The json-type of messages are string matched at the start
* Json CMD, history-format string and RTD fields are all **case-sensitive**
```sh
C++ case-sensitive Raw string match example for performance
R"([{"n")"     // Realtime Data
R"({"cmd")"    // Commands
R"({"hist")"   // Historical Data
R"({"info")"   // Symbol Information v3.02.11
R"({"ed")"     // Extra Data v3.03.16
```

## Database Plug-in Commands
Explained here [Amibroker Forum](https://forum.amibroker.com/t/documentation-on-batch-data-plugin-command/39269)
Amibroker [Batch window manual](https://www.amibroker.com/guide/h_batch.html)

Every time the Plug-in receives data, it stores is internally in its own temporary storage and notifies Amibroker of new data. Unfortunately, by design, if the Symbol is not being used by the user in any way, the plug-in may never be able to "push" the data to AB local Database that is persistent.
Therefore, user needs to use a Batch file that consists of an empty Analysis Exploration to force all symbols to fetch data. More on this later.

These are some ways to communicate with the Plug-in from the Amibroker User-Interface OR when the websocket is shutdown and therefore not reachable externally.

##### 1) PushDBtoAB
Batch command to inform plug-in that an all symbol fetch has been performed.

##### 2) ConnectPlugin
Batch command to start the Websocket connection.

##### 3) ShutdownPlugin
Batch command to stop the Websocket connection.

##### 4) DbStatus
Batch command to log some Plug-in statistics.
```sh
[1] DBG: Db() Status Map_size=4, Qt_RingBufr=200, SymList=SYM1,SYM3,SYM4,SYM5,
```
##### 5) Clear First Access/Automatic backfill data
For every first access of a symbol, bfauto or bffull request is sent once only. You can clear the flag with this.

< Add more commands as required>

## Logging and troubleshooting
#### 1) DebugView
WS_RTD uses extensive logging using Windows Debug output.
- Just run [DebugView](https://learn.microsoft.com/en-us/sysinternals/downloads/debugview)
- Set the Filter to "DBG" *(may change this string later)*
- View realtime Plug-in related information here

[![img dbgview11](https://github.com/ideepcoder/Rtd_Ws_AB_plugin/blob/main/images/help/debug1.png?raw=true)]

#### 2) One or some symbols not updating
Check under Symbol > Information window,
```sh
Use only local database = No    (Ensure No, If yes, plug-in-cannot update it)
```

#### 3) View Count of bars that are in Plug-in DB and those that have been updated to Amibroker DB
Whenever new data arrives, whether RTD or Historical, it is immediately stored internally. Amibroker is notified, but AB will choose to to request data only when that symbol is being used.
To visualize that, currently, Two fields in the AB REaltime Quote window are dedicated to that.
```sh
EPS: This column shows the Total count of bars in Plug-in DB
```
```sh
Dividend: This column shows the Total count of bars in updated to AB from the Plug-in DB
```
[![RT window1](https://github.com/ideepcoder/Rtd_Ws_AB_plugin/blob/main/images/help/RT_Data_index.png?raw=true)]

#### 4) AB Plug-in UI Commands: Connect and Shutdown
These commands will only Connect or Disconnect the plug-in (Client Websocket) to the local relay server. Data stored in the Plug-in DB is not affected.
AB Symbols will still get updated if there is fresh data in the plug-in DB while the user has disconnected the plug-in.
The plug-in DB is not persistent, that means, if user Exits Amibroker or Changes the Current DB in Amibroker, only then the plug-in data is cleared.

#### 5) Sample output of Configure settings
```sh
DBG: ConfDlg() RI=300ms, Conn=127.0.0.1:10101, SymLimit=1000, QuoteLimit=250, DbName=Data
```
< more items to come >


# WS_RTD Plugin Settings storage
The plugin stores settings in the Windows Registry like Amibroker QT.dll
Amibroker path
```sh
Computer\HKEY_CURRENT_USER\SOFTWARE\TJP\wsRtD
```
```sh
Nested in TJP\wsRtD\<Database_name>
```
Settings will be UNIQUE to each unique database name created in AB.
ALL Amibroker Databases that share common Database name but are different filesystem path will "still" share the same settings.
This is the best of both, allows the user to separate or share settings as required.
```sh
Example 1:
Amibroker DB name: Data with their respective paths
C:\sample1\Data
D:\archive\old_sample\Data
```
*Both AB DBs above will share the same settings and there will be only one registry key named "Data"*
```sh
Example 2:
C:\sample1\Data_rtd
C:\sample1\wsrtd
```
*Data2 and wsrtd will be a new entries and each can have its own settings*
Image of Windows Registry below:

[![img sample_server1](https://github.com/ideepcoder/Rtd_Ws_AB_plugin/blob/main/images/help/TJP_Registry.png?raw=true)]



## Client-Data Sender application
For production release:
```sh
To do:
For now, this integration depends on the user and technical skill
Client-sender program should be developed using Vendor specific library.
Working on providing a Relay Server
```

> Note: `--rolesend` is required for client-sender identification

Example rolesend: data vendor / broker client program / Python sample server

> Note: `--rolerecv` is required for client-receiver identification

Example rolerecv: Ws_Rtd plugin or ArcticDB data collection socket conn

Verify the connection by navigating to your terminal running the server

```sh
127.0.0.1:10101
```
#### 1) Specifics of Client-Sender Application
The design itself keeps in mind a minimal requirement so the application just needs to conform with the fol1owing:
- Client-Sender connects to the matching websocket port
- On connection, it sends the above simple string "rolesend" before any other data
- Then it follows the json-RTD format for realtime bars matching the interval set in AB configure DB
- To handle Requests from Data Plug-in, it will receive the json-CMD or json-Hist. It should respond with the appropriate json formats described above. That's it.
- The Advantage of using a relay server is that when either Plug-ins or Client applications reconnect or disconnect, they don't cause the other party websocket drop errors which is distracting as well.

< more documentation on this later >
The Programming Language of choice or platform does not in any way become restrictive to the user.

# FAQs
#### 1) Can I Backfill data when the Status is Shutdown?
As the websocket is disconnected, no commands can be sent or received, therefore it is not possible.
However, Data available inside the plugin-DB can still be accessed for symbols to get updated.

#### 2) I Imported data using Amibroker ASCII Importer, now I have duplicate or Corrupt data.
By design, it is up to the user to ensure that duplicate data is not imported. Mixing two different methods can cause unwanted behaviour.
You can delete all the data and import it afresh.
Some steps are taken when using plug-in to overwrite duplicate data.
However, this Plug-in is quite technical and for performance, the user's Client side application should ensure data integrity.

#### 3) Some of my Symbols are not updating with data but my Server shows that data for RTD is generated.
Ensure that under Symbol Information window in Amibroker, the setting "Use local database only" is set to No. If yes, Plug-in cannot update to it.

#### 4) How do I ADD symbols in AmiBroker?
When new symbols arrrive in the plugin-DB, the plugin status will be dark Green in colour. You can go to Configure settings Dialog and Click RETRIEVE Button. Symbols will automatically get added.

[![Retrieve](https://raw.githubusercontent.com/ideepcoder/Rtd_Ws_AB_plugin/refs/heads/main/images/help/Retrieve.png)]

The status color will change to &#128994; from $${\color{ForestGreen}Dark \space Green}$$

#### 5) Settings change in Configure
Kindly use DebugView to check if settings change requires an AB to be restarted or Plugin to be reconnect. Scroll up to Configure section and read the details.


## AFL access functions
### using GetExtraData()
https://www.amibroker.com/guide/afl/getextradata.html

#### 1) "IsRtdConn"
if Data plugin websocket is connected, 1 else 0

#### 2) "ClientAppStatus"
if Client App websocket is connected, Client App should implement "cping" cmd
```sh
0 = client-app not running
200 = running
400 = running but remote disconnected
-1 = ping sent, awaiting reply
```

#### 3) "Custom FieldNames"
Refer to the Extra Data section, plugin supports full custom data per symbol.

#### 4) "AddSymSYMBOL_NAME"
addsym cmd for a specific Symbol can be triggered from AFL. Useful when creating dynamic symbols.
For example, Subscribe RTD for ATM options from current Spot price.

#### 5) "RemSymSYMBOL_NAME"
remsym cmd for a specific Symbol can be triggered from AFL. Useful to unsubscribe RTD symbols in CLIENT-APP.


<here>

## Development
Want to contribute? Great!
##### A)
For now Clent-sender applications have a lot of scope for expansion
Current Relay Server is python-based.
Client-sender can be in a Programming Language of your choice or using Data Vendor library,
these applications can be expanded greatly to encompass various Brokers APIs and Data Vendors.
##### B)
WS_RTD uses C++ for development, strongly based on ATL/MFC, but is currently closed.

## License
**To be decided**

This LICENSE Section alongwith the CREDIT and AUTHOR Section at minimum should be distributed EXACTLY as-is when distributing a copy of the data-plugin binary or DLL.

## Author
NSM51
A fan and avid Amibroker user.
https://forum.amibroker.com/u/nsm51/summary
< Journey story about the idea of this plugin >

# Tech & Credits:
## AB Data Plugin
Inspired by QT.dll sample from AmiBroker ADK
https://gitlab.com/amibroker/adk/-/tree/master/Samples/QT  
Credits: [Amibroker] Company & Dr. Tomasz Janeczko

## Web Socket
Current WS library: EasyWsClient
https://github.com/dhbaird/easywsclient  
License: MIT  
Works well as light-weight windows WinSock2 wrapper.
Credits: dhbaird  

## JSON
Current JSON library: RapidJson
https://github.com/Tencent/rapidjson  
License: MIT  
Credits: Milo Yip  
RapidJson is benchmarked as fastest.

## WS Class and Queue inspiration
https://stackoverflow.com/a/69054531, Credits: Jerry Coffin 

*Created using* [Dillinger]

###### Doc End
[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job. There is no need to format nicely because it shouldn't be seen. Thanks SO - http://stackoverflow.com/questions/4823468/store-comments-in-markdown-syntax)

   [Amibroker]: <https://www.amibroker.com>
   [Dillinger]: <https://dillinger.io/>
