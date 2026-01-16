# WS_RTD_AB
## _AmiBroker Realtime data plugin using Websocket and JSON based communication_

[![Build Status](https://raw.githubusercontent.com/ideepcoder/Rtd_Ws_AB_plugin/84c47468847d2bbf53d2f12fa110d13c041d7b2d/images/unknown.svg)](https://github.com/ideepcoder/Rtd_Ws_AB_plugin)
Doc version: 1.3, Plugin: 3.06.26
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
- Supports plugin state persistence, restores data between DB changes and AB restarts. v3.04.20
- LRU Manager, Least Recently Used symbols can be auto evicted. v3.05+
- Supports lowest 1-second base time interval and higher
- GetExtraData improvized for COMMUNICATION/Trading interface alongwith BrokerWS standalone
- Mixed Mode Data support for RTD-Intraday and EOD historical data. Big enhancement! v3.06+
- Aggregate Partial Backfill feature enhancement. v3.06+


# ✨ Upcoming  ✨
- Check out the Upgrades section at the end for performance enhancements
- ArcticDB active integration
- A lot of leverage with keeping bloated data locally in ArcticDB and a concise Amibroker database


### Table of Contents and Anchor links
| -  | Topic / Link | Description |
| -  | ------ | ------ |
| 01 | [Sponsorship](#14-why-the-sponsorware-model)| Appeal for a sustainable project |
| 02 | [Installation](#installation) | How to configure/setup |
| 03 | [Plugin Settings](#configure-the-plug-in) | Plugin settings explained in detail |
| 04 | [RTD Format](#1-rtd-format-in-json-message) | RTD format in JSON structure |
| 05 | [Backfill Format](#2-History-format-in-json-message) | Historical data format in JSON structure |
| 06 | [CMD Format](#3-cmd-format-in-json-message) | Command format in JSON structure |
| 07 | [ACK Format](#4-ack-format-in-json-message) | Acknowledge format in JSON structure |
| 08 | [INFO Format](#5-info-format-in-json-message) | STOCK-INFO format in JSON structure |
| 09 | [GetExtraData Format](#6-extra-data-format-in-json-message) | EXTRA-DATA for Fundamental, Trading interface, Custom indicators or Extra data |
| 10 | [JSON Format begin note](#important-json-string-compression-and-format) | Important string matching & compression for JSON  |
| 11 | [Plugin Commands](#database-plug-in-commands) | Using UI or AB Batch for plugin commands/control |
| 12 | [Debugging](#logging-and-troubleshooting) | Logging and Troubleshooting |
| 13 | [Backfill Styles](#backfill-style-01) | Performance note on various Backfill algorithms |
| 14 | [WSRTD Settings storage ](#wsrtd-plugin-settings-storage) | Windows Registry usage for saving plugin settings |
| 15 | [Client-App](#client-data-sender-application) | Client App role for Relay server |
| 16 | [FAQs](#faqs) | Frequently asked questions - Must read |
| 17 | [LRU](#16-lru-manager-usage) | Least Recently Used symbol automatic eviction |
| 18 | [AFL Access](#afl-access-functions) | AFL Access functions to plugin |
| 19 | [Upgrades](#upgrades) | Version wise Feature Upgrades/DevLog |
| 20 | [Credits](#tech--credits) | Credits for other Authors and Contributors |
| 21 | [Future Plans](#planned) | Exciting upgrades that are planned |


##### For DLL/Binary redistribution, kindly read the LICENSE section.
============================================

## Installation

WSRTD requires [AmiBroker] to run.
| Software | Supported / Tested version |
| ------ | ------ |
| AmiBroker | v6.30+ x64-bit |
| Visual C++ | VC++ 2022 redistributable |
| Windows OS | Windows 10/11 x64-bit |
| Linux OS| To-Do, untested |
| Vanilla Python | [3,12 x64-bit](https://www.python.org/downloads/release/python-3120/) or higher |
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
Base time interval: 1 minute or as suited ( minimum 1-second v3.05+ )
```
*To-Do: Tick-data unsupported for now*

[![img create](https://github.com/ideepcoder/Rtd_Ws_AB_plugin/blob/main/images/help/DB_Create.png?raw=true)]

##### Configure the Plug-in
```sh
Click Configure button
```

[![img configure](https://github.com/ideepcoder/Rtd_Ws_AB_plugin/blob/main/images/help/Plugin_Configure3.26.png?raw=true)]

- The internal plug-in DB stores RTD Quotes as a Fixed-Size BUFFER. Max_Num_Sym_Quotes here means the number of bars to hold(cache) "per symbol". If you run any Analysis frequently and ensure all symbols are accessed, then you can set it as low as 10 to reduce memory usage. Each bar is 40 KB.
- Timer Interval: The frequency at which incoming json data is processed. Optimize depending on your CPU, but 300ms is sufficient.
- CPing: When enabled, sends a periodic ~90s heartbeat message to CLIENT-APP
- Auto-save Plugin DB: This feature enable state persistence between AB restarts. Plugin data like ExtraData, Symbol Map and Fundamental data are stored.
- Auto-save pending BF: By default, pending backfill data is discarded when AB shuts down. This option allows to save backfill history not yet merged into AB DB.
- Auto-del LRU: This enables LRU, Least Recently Used symbol eviction. When MAX_NUMBER_SYMBOLS is reached, oldest ticker is evicted if new one arrived.
- EOD Mixed-Mode: This enables AB style mixed mode bars for EOD data. Read Backfill to understand more.
- Merge Partial Backfill: Two backfill philosophies: when unchecked, only one or most recent json-hist is cached. If enabled, Client-App can send multiple packets in oldest to newest order and plugin will aggregate them. Read backfill section for details.
- Save: Ensure to click, if any text or checkbox settings are changed.
- Close: Exit Configure Dialog without saving any settings if changed.
- Retrieve - The AB prescribed way to update or Add new symbols into AB DB.


#### Important Settings change:
1. **Max_Num_SYM_Quotes** : Requires AB restart
2. ***Changes in IP / Port / AUTH** : Requires Plugin shutdown / connect, ie. Reconnect. 
3. Toggling EOD Mode from on to off can lead to data corruption, as each EOD bar is inserted after all intraday bars of the same Date
4. Merge partial backfill relies on SORTED Arrays, ensure to send oldest to newest data even though Internal path performs sorting and deduplication.

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
There are various types: Json-RTD, Json-HIST, Json-CMD, Json-ACK, Json-INFO, Json-ED

### 1) RTD format in json message
Currently, minimum periodicty/timeframe/interval of bars is 1 minute.
(Note: v3.05+ supports 1-second base time interval)
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
'd','t','as','bs' as integer,
float is safe for the rest.
To-do: unix timestamp(u/g), microseconds interval

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

 **ORDER** The sequence of columns in historical data can be anything set by the user, but it has to match its character in the Format specifier string. The beginning of the json message will start with "hist" containing Symbol name followed by "format" field containing the Format specifier string.
 
 **Important: History Array records must be in ascending order**, ie. Least DateTime first.
 v3.06+ bring Mixed Mode, ie. "mixed intraday EOD/intraday" mode.
```sh
(ugdt)ohlcvixy
milliseconds not yet supprted
u = unix timestamp localtime()   ( type: integer64 )
g = unix timestamp gmtime()      ( type: integer64 )
d = date                         ( type: integer )
t = time                         ( type: integer )
u, g and d are MUTUALLY EXCLUSIVE, but any one is mandatory.
"t" is mandatory for intraday bars with "d"
ONLY "d", omitting "t" ( V3.06+ mixed mode )

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
Currently, Vendor backfill means N most recent days data
so plugin also sets Bars from the first of this Array to the last bar
the existing bars are overwritten, from first bar of hist.
old_data + WS_data
Now, backfill means old_data + backfill (upto last backfill)
then, old_data + backfill_data + Rt_data ( from bars after last backfill bar, if any )

[![img sample_server1](https://github.com/ideepcoder/Rtd_Ws_AB_plugin/blob/main/images/help/menu_activesym.png?raw=true)

##### Backfill style-02
If your vendor restricts backfill length, then request oldest data chunks and progress to newer ones.
Sending newer chunks first like in reverse order will sort, deduplicate and merge but it is not cpu optimal.

v3.06+ introduces Merge Partial Backfill option. You can send multiple json-hist that will be aggregated in Plugin DB BUT it is ascending timestamp order.
That means like before, OLDEST data first progressively sending newer data.
It is still wiser to keep a dummy AFL/Analysis Scan to ensure timely update to AB DB instead of storing in plugin DB.

##### Mixed Mode v3.06+ Intraday + EOD
Mixed mode allows supplying **both intraday and End-of-Day (EOD)** bars for the same ticker.
This data cannot be supplied as RTD messages. One has to use backfill/json-hist as it is considered logical history.
To maintain full backward compatibilty, nothing is changed, the format is mandatorily "d", like "dohlcv", optional: i,x,y 

Be aware that some vendors may send today's daily EOD bar while ticker has RTD, this puts wrong EOD bar at the end. Be sure to skip this bar before forwarding data to plugin.

NOTE: Backfill style-01 is relatively faster then MIXED-MODE OR MERGE_PARTIAL_BACKFILL mode. The merge algorithim is fast, 100K bars in 1ms on average 3GHz cpu, but it still requires bar by bar comparison.
```sh
{"hist":"SYM1","format":"dohlcv","bars":[...]}
```


### 3) CMD format in json message

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
It is optional heartbeat packet that just says plugin is active in AB.


##### g) Extra-Data request for Symbol
{"cmd":"ed","arg":"SYMBOL_NAME"}
```sh
{"cmd":"ed","arg":"SYM1"}
```
Extra-Data json has been requested for the particular Symbol by the Plugin.
User can return relevant json-ed. Look at Extra-Data Format for more information on allowed types.


##### h) EOD ALL symbol backfill
{"cmd":"bfeodall","arg":"x"}
```sh
{"cmd":"bfeodall","arg":"x"}
```
Only if mixed-mode is enabled.
For ALL Symbol backfill, client application should still send individual Json-hist messages for each symbol.


##### i) EOD single symbol backfill
{"cmd":"bfsymeod","arg":"reserved SYMBOL_NAME int_preset"}
```sh
{"cmd":"bfsymeod","arg":"y SYM1 1"}
```
Only if mixed-mode is enabled.
int_preset is 1 or 2, signalling short or long duration that suits client-app.


#### 3.2) Response CMD "to WSRTD" Plug-in from Server

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


#### 3.3) Request CMD "to WSRTD" Plug-in "from" Server
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
returns {"ack":"dbgetlist","code":200,"arg"="AA,AAPL,AXP,BA,C,CAT,IBM,INTC"}
```
v3.05+ returns unsorted list, maintains the insertion order from earliest to most recent.


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
The Data is persistent "only" if auto-save is enabled.
FieldNames starting with "_" underscore are reserved for plugin use. Do not prefix CUSTOM_FIELDNAMES with underscore.

Individual fields are not updated, the entire string is replaced with the new json-ed packet.

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
"EdDate", "EdTime", "EdStatus", "EdFields", "CUSTOM_FIELDNAME", 
```
Reserved Control commands are prefixed with underscore, they send json-cmd to Client-App:
```sh
"_AddSym". "_RemSym", "_NewReq", "_EdRequest", "_IsRtdConn", "_ClientStatus",
```


1) Date and Time - "EdDate" and "EdTime"
returns float similar to DateNum() and TimeNum() or 0.
This polling is fast, which gives the Last Update Time of ExtraData json.
It prevents unnecessary lookups and you can cache your AFL data in StaticVariables.

2) ExtraDataStatus - "EdStatus" 
Returns Count of FieldNames for current Symbol, else returns 0, if no fields exist.
One can use this to check before request json-ed command via ExtraDataRequest.

3) ExtraDataFields - "EdFields"
Returns a comma-separated string containing valid/available "FieldNames" for the symbol, else returns 0.
It can be used in AFL to query valid FieldNames as each symbol supports custom extra data fields.

4) CUSTOM_FIELDNAME - 
Pass the custom fieldname to access data and use in your AFL.
If FieldName is not found, -1 is returned (float).

5) ExtraDataRequest - "_EdRequest"
Sends a json-ed request with current symbol to the CLIENT-APP.
AFL can be used to request data when required.

6) _NewReq<> = prefix for custom string payload

*See the AFL access functions sections for detailed usage.


Note: If you are using v3.02.11, the commands "do not" have underscore prefix.
So use as "addsym", "remsym" and custom fields are not supported.

## Important: JSON string compression and format
* Json message should be compressed removing all whitespaces or prettify.
* Use your library Json Encoder to prevent errors.
For example, *The JSON standard requires double quotes and will not accept single quotes*
* The json-type of messages are string matched at the start
* Json KEYS are all **case-sensitive**, unless specified otherwise
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



## Logging and troubleshooting
#### 1) DebugView
WSRTD uses extensive logging using Windows Debug output.
- Just run [DebugView](https://learn.microsoft.com/en-us/sysinternals/downloads/debugview)
- Set the Filter to "DBG" *(may change this string later)*
- View realtime Plug-in related information here

[![img dbgview11](https://github.com/ideepcoder/Rtd_Ws_AB_plugin/blob/main/images/help/debug1.png?raw=true)]

#### 2) One or some symbols not updating
Check under Symbol > Information window,
```sh
Use only local database = No    (Ensure No, If yes, plug-in cannot update it)
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
The plug-in DB is not persistent, that means, if user Exits AmiBroker or Changes the Current DB in Amibroker, only then the plug-in data is cleared.

#### 5) Sample output of Configure settings
```sh
DBG: ConfDlg() RI=300ms, Conn=127.0.0.1:10101, SymLimit=1000, QuoteLimit=250, DbName=Data
```
< more items to come >


# WSRTD Plugin Settings storage
The plugin stores settings in the Windows Registry like other ADK plugins.
AmiBroker path
```sh
Computer\HKEY_CURRENT_USER\SOFTWARE\TJP\WsRtD
```
```sh
Nested in TJP\WsRtD\<Database_name>
```
Settings will be UNIQUE to each unique database name created in AB.
ALL AmiBroker Databases that share common Database name but are different filesystem path will "still" share the same settings.
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

Example rolerecv: WsRtd plugin or ArcticDB data collection socket conn

Verify the connection by navigating to your terminal running the server

```sh
127.0.0.1:10101
```
#### 1) Specifics of Client-Sender Application
The design itself keeps in mind a minimal requirement so the application just needs to conform with the fol1owing:
- Client-Sender connects to the matching websocket port
- On connection, it sends the above simple string "rolesend" before any other data
- Then it follows the json-RTD format for realtime bars matching the interval set in AB configure DB
- To handle Requests from Data Plug-in, it will receive the various specified json-requests. It should respond with the appropriate json formats described above. That's it.
- The Advantage of using a relay server is that when either Plug-ins or Client applications reconnect or disconnect, they don't cause the other party websocket drop errors which is distracting as well.

#### 2) Building bars in Client-App 
For improved performance, your data vendor gives you an SDK library.
In python for example, use a Pandas table, like in the Client Class sample, and then perform snapshotting every 0.9sec or so.
Basically, your RTD messages should be an array of all ticks in that second for all tickers that ticked.
If you use 1-min timeframe as base, then you can use the logic to build 1-min bars from the same sample.

Avoid 1-sec DB unless your strategies specifically require it, because AB tends to load the whole symbol data in RAM.
Also, most vendors provide 10year data in 1-min, so it keeps your DB consistent.
AB requires all bars to be only in the base time interval selected during DB creation.

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
Note: Symbols cannot be automatically added/removed or StockInfo updated without clicking RETRIEVE, this is by AB design.

#### 5) Settings change in Configure
Kindly use DebugView to check if settings change requires an AB to be restarted or Plugin to be reconnect. Scroll up to Configure section and read the details.

#### 6) Percentage change in RTQ(realtime-quote) window does not update? other columns are ok.
You need to check and send the "pc" key in RTD, pc is previous close which is required to compute it.

#### 7) I need to paginate HISTORICAL backfill for symbol(s), but data is inconsistent?
While backfilling, most recent quotes are retained. For pagination or partial backfill, start from the oldest data and then supply newer ones.
Many vendors restrict the number of bars fetched from server, so start with oldest batch and progressively send newer data.
The plugin caches only 1 json-hist, so you need to run Explore on all those symbols before send history data again.
Another option is to collect all the data in Client-App and then send it once to the plugin.
Ensure DB settings has sufficient bars.

v3.06+ introduces Merge Partial Backfill option. You can send multiple json-hist that will be aggregated BUT it is ascending timestamp order.
That means like before, OLDEST data first progressively sending newer data.

#### 8) Older bars are getting overwritten or data is being lost?
AB will store ONLY the number of maximum bars specified in DB settings. Adjust to suit your needs.

#### 9) What is the Max number of Symbol Quotes in plugin settings window?
Plugin is designed to be memory efficient. It retains or caches only the "n" most recent bars specified here.
If you are running Analysis very frequently, you can reduce the number of bars to cache.
The default is 200 bars, for a typical day of RTD in 1-min resolution.

#### 10) Do you provide 32bit plugin?
ALL AB versions are available in both 32bit/64bit, and the 32bit AB was mostly limited by older 32bit "only" plugins from vendors, or old OS.
Since AB and WsRTD are both 64bit, you can leverage all the advantages of a 64bit Operating System like windows 10 or higher.

#### 11) Client-App is receiving too many backfill requests?
By design, the plugin websocket drop is interpreted as internet disconectivity or interuption.
Ideally, you should use the RELAY Server model, where the server and AB can be up and connected for months without restarting.
If you are frequently disconnecting either, plugin requests backfills as the completeness of current data state is not known.
BFFULL and BFAUTO commands are sent only once on first use in AB, until any disconnection occurs that resets this flag.

#### 12) "Chng" and "% Chng" in Realtime Quote window are not updating?
You need to provide "pc", ie. previous-close price in the json-RTD packets.
Similarly, you can send DH,DL,DO which refer to Day High, Day Low and Day open, used in RTQ window.

#### 13) What do I need to know about Plugin State persistence?
From v3.04.20, the plugin saves the plugin-DB state in binary format in the AB CWD.
It is of the format "WsRTD_DBNAME_PLUGINVERSION.bin"
State is reloaded only for same DB_NAME and PLUGIN_VERSION and Max_Quote_Size.
This file is created automatically when AB is exited or AB-DB is changed.
The file is read and loaded when the same DB in the CWD file is found.

It just stores the RTD, Backfill, Extra data, Recent_Info and Stock_Info related data.

One drawback introduced, is bfauto is not re-sent because plugin detects existing RTD,
so if you reload in live market, make sure to backfill.
During closed market hours, it wont matter.

Also, if you DELETE symbol in AB UI, make sure to send {"cmd":"dbremsym"..} to clear from plugin-DB,
else this ticker will remain cached and use up Symbol_limit.

Pending Backfills, which means data in plugin-DB not yet merged with AB DB, is not saved in Auto-save by default.
You can enable in UI settings, but be warned, this can introduce corruption if Merge Partial Backfill is also enabled.

#### 14) Why the Sponsorware model?
For over a year, I have been helping users with updating and improving the plugin.
Also helped and continue helping with client-app code.
Given the amount of time it takes, it is not viable to continue forever.

The original plugin and all feature updates upto version 3.02.11 will be available for free as it is presently.
No restrictions and users are free to evaluate or use for free forever under NON-COMMERCIAL USAGE.

Newer versions will rely on sponsor/donate as I am not putting a fixed price.
Because it is not only the plugin, but alot of client-app code that I help them with.
None of the plugin uses https/remote server communication etc to keep privacy first, there is a small license file, that user sends the code, it is signed and sent back. (completely offline)
Code is reviewed by AmiBroker Company. *applied, pending response

I intend to continue supporting the AmiBroker community as best as I can.

#### 15) I am upgrading my hardware, what about my License?
Just get in touch, all sponsors are greatly valued and your issues will be sorted. 

#### 16) LRU Manager usage
This is an automatic Least Recently Used (LRU) symbol evictor from the plugin-DB. If MAx_LIMIT of PDB is reached, users without LRU enabled will get an orange Notify status and with it enabled, LRU drops older symbols for new ones.
To improve Index rebuild rate which can be cpu consumning, currently an 8MIN window is used for re-indexing.
You may have a look at it in the cpp source folder.

#### 17) I want to clear Plugin-DB or Delete all entries of Ticker cache?
From AB UI, ENSURE that plugin is SHUTDOWN, to enable menu entry for "DbRemSym ALL".
This clears plugin cache without having to restart AB.
For individual Ticker deletion, see DbRemSym json-cmd or the Active-Symbol menu item (when shutdown).
Also, If State-Persistence is enabled, ensure to manually delete file from AB working directory else it will be re-imported at startup.
 
#### 18) 


## AFL access functions
### using GetExtraData()
https://www.amibroker.com/guide/afl/getextradata.html

To fine tune the hotpath, underscore prefix is used to distinguish control commands vs faster plugin-memory lookups.
bad key type, special return -2.0 as float in AFL

Note: If you are using v3.02.11, the commands "do not" have underscore prefix.
So use as "addsym" or "remsym". New commands and Custom_Fields are not supported in v3.02 or lower.

#### 1) "_IsRtdConn"
if Data plugin websocket is connected, 1 else 0

#### 2) "_ClientStatus"
if Client App websocket is connected, Client App should implement "cping" cmd
```sh
0 = client-app not running
200 = running
400 = running but remote disconnected
-1 = ping sent, awaiting reply
```

#### 3) "Custom FieldNames"
Refer to the Extra Data section, plugin supports full custom data per symbol.
This is specifically a case-sensitive match.

#### 4) "_AddSymSYMBOL_NAME"
addsym cmd for a specific Symbol can be triggered from AFL. Useful when creating dynamic symbols.
For example, Subscribe RTD for ATM options from current Spot price.
```sh
GetExtraData("_AddSymNEW_TICKER100");	// sends an "addsym" command for "NEW_TICKER100" to Client-App from AFL
```

#### 5) "_RemSymSYMBOL_NAME"
remsym cmd for a specific Symbol can be triggered from AFL. Useful to unsubscribe RTD symbols in CLIENT-APP.
```sh
GetExtraData("_RemSymNEW_TICKER100");	// sends a "remsym" command for "NEW_TICKER100" to Client-App from AFL
```

#### 6) "_NewReqCUSTOM_REQUEST"
newreq is for "New Request", where a custom string can be sent to the server from AFL.
Generally, AFL is not used to communicate with data plugin, but this is non-blocking and a method to communicate
with the Client-App from AFL.
Data received as "Extra Data" from Client-App can later be read and used in AFL.
```sh
GetExtraData("_NewReqTICKER100,Buy,50,10");	// sends a "newreq" string as "TICKER100,Buy,50,10" to Client-App from AFL
```
AB has a more advanced Trading Interface, derived from BrokerIB(AB) called BrokerWS which is the documented way to deal
with realtime order information.


Note: Use AFL=>Static Variable guards around GetExtraData() & GetExtraDataForeign() to prevent multiple requests / processing which may be unnecessary.
Also use "EdTime" and "EdDate" to query when last status was updated which is fast.
[AFL sample for querying GetExtraData()](https://github.com/ideepcoder/Rtd_Ws_AB_plugin/blob/main/Samples/AFL/ExtraData_1.afl)

<here>

## Plugin Menu options
[![img sample_server1](https://github.com/ideepcoder/Rtd_Ws_AB_plugin/blob/main/images/help/plugin_main_menu.png?raw=true)

# Upgrades:
- Version 3.04+ introduces a new network rewrite technique for JSON parsing that improves performance over the already fast original stack.
- Version 3.05+ introduces a robust, private, secure and offline usage model.
- Version 3.05+ implements LRU, Least Recently Used Manager. In the event of max symbol limit hit, oldest symbols are automatically deleted in plugin DB.
- Version 3.06+ implements sub 1-minute time interval, the lowest ie. 1-second.
- Version 3.06+ implements AB Mixed Mode for both Intraday and Historical EOD data in same DB.
- Version 3.06+ sorting and deduplication of timestamps for BackFill arrays if Either Mixed-mode OR Partial Backfill is enabled.(a bit more cpu usage)
-

# Planned:
- Version 3.07+ implements true tick-by-tick data support, including resolving multiple same timestamp trades & out-of-order ticks.

## Development
Want to contribute? Great!
##### A)
For now Clent-sender applications have a lot of scope for expansion
Current Relay Server is python-based.
Client-sender can be in a Programming Language of your choice or using Data Vendor library,
these applications can be expanded greatly to encompass various Brokers APIs and Data Vendors.
##### B)
WSRTD uses C++ for development, strongly based on ATL/MFC, but is currently closed.

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
