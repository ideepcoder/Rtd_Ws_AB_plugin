/*/////////
*	Author: ideepcoder
*	Date: 20251212
*	LRUManager.cpp
*	Build Least Recently Used ticker/symbol for evict_when_map_full in pro features.
*///////////

// LRUManager.cpp
// 

/////***** FULL Documentation at the end after cpp code *****\\\\\

#include "stdafx.h"
#include "LRUManager.h"


/// <summary>
/// struct function for comparison, overloads the function-call operator ()
/// </summary>
/// <param name="a"></param>
/// <param name="b"></param>
/// <returns></returns>
bool LRUEntryCmp::operator()( LRUEntry const& a, LRUEntry const& b ) const {
    if ( a.date != b.date ) return a.date < b.date;
    // relying on CString operator<; it is valid for ADK date packing
    return a.key < b.key;
}



// ctor takes reference to underlying map so it can extract Date values when building/updating
LRUManager::LRUManager( TickerMap& mapSym )
    : m_mapSym( mapSym )
    {
        // RebuildIndex();  // can cause double rebuild, rebuild explicitly.
    OutputDebugString( "DBG: LRU() init" );
    }


LRUManager::~LRUManager() = default;


// Rebuild index from scratch
void LRUManager::RebuildIndex() {

    OutputDebugString( "DBG: LRU() Rebuild" );
    m_index.clear();
    m_lookup.clear();

    for ( auto& pair : m_mapSym ) {
        const CString& key = pair.first;
        uint64_t date = ExtractDateForKey( key );
        InsertEntry( key, date );
    }
}

// Call this whenever the ticker for 'key' has a new last-quote or its IdxQEx changes.
// If key is new it will be added.
void LRUManager::AddOrUpdateKey( const CString& key, uint64_t newDate ) {

    auto itLook = m_lookup.find( key );
    if ( itLook != m_lookup.end() ) {

        //// already the same recency, no need to waste cpu
        //if ( itLook->second->date == newDate )  return;
        //// If dates are within the window, dont recompute Eviction index
        if ( ( itLook->second->date & MASK_8MIN ) == ( newDate & MASK_8MIN) )   return;

        // remove old entry then re-insert
        m_index.erase( itLook->second );
        m_lookup.erase( itLook );
    }

    InsertEntry( key, newDate );
}

// Remove key from index (call when symbol removed from MapSym)
void LRUManager::RemoveKey( const CString& key )    {
    
    auto itLook = m_lookup.find( key );
    if ( itLook != m_lookup.end() ) {
        m_index.erase( itLook->second );
        m_lookup.erase( itLook );
    }
}

// Returns true if we evicted at least one symbol. For each eviction, OnEvictSymbol(key) is called.
// Evicts until MapSym.size() <= maxSize.
int LRUManager::EvictIfOverLimit( size_t maxSize ) {

    int evicted = 0;

    while ( m_mapSym.size() > maxSize ) {
        
        if ( m_index.empty() ) {
            evicted = -1;
            break; 
        }// nothing to evict (should not happen if sizes mismatch)
        
        // smallest = begin()
        const CString keyToEvict = m_index.begin()->key;

        // Call user-implemented eviction handler (placeholder below)
        bool keyDeleted = DbRemoveSymbol( const_cast<CString&>( keyToEvict ) );
        if ( keyDeleted ) ++evicted;

        // remove from LRU structures // RemoveKey() called from DbRemoveSymbol()

        OutputDebugString( "DBG: LRU() removed " + keyToEvict );
    }
    return evicted;
}

#ifdef _DEBUG
    // Debug helper: print LRU index (optional)
    void LRUManager::DebugPrintIndex() const    {
        CString t{ "LRU index (oldest first):" };
    
        for ( auto const& e : m_index ) {

            t.Format( "[%llu] %s", e.date, e.key.GetString() );
        }
    }
#endif


///// PRIVATE FUNCS ////////

// Helper: safely extract the 64-bit date for a given symbol key in the map.
// If ticker missing, pRtQtarr missing, or IdxQEx == -1, returns 0 (smallest) so it becomes highest-priority deletable.
uint64_t LRUManager::ExtractDateForKey( const CString& key ) const {
    auto it = m_mapSym.find( key );
    if ( it == m_mapSym.end() ) {
        return 0ULL;
    }
    Ticker* pT = it->second;
    if ( !pT ) return 0ULL;
    if ( pT->IdxQEx == -1 ) return 0ULL;        // 0=0ULL no compiler warning

    CQuoteArray* pArr = pT->pRtQtarr;
    if ( !pArr ) return 0ULL;

    int idx = pT->IdxQEx;
    if ( idx < 0 || idx >= pArr->GetSize() ) return 0ULL;

    const Quotation& q = pArr->GetAt( idx );
    // treat q.DateTime.Date as unsigned 64-bit integer
    uint64_t d = static_cast<uint64_t>( q.DateTime.Date );

    return d;
}


// insert entry into set and store iterator in lookup
void LRUManager::InsertEntry( const CString& key, uint64_t date )   {
    
    LRUEntry e{ date, key };
    std::pair<
        std::set<LRUEntry>::iterator,
        bool
    > result = m_index.insert( e ); // returns: second->true if new,false if existing.

    // Always update lookup to point to the set entry
    m_lookup[ key ] = result.first;
}


/////***** Documentation *****\\\\\

// LRU recency is bucketed (~8 minutes).
// Within a bucket, eviction order is deterministic but not usage-precise.
// RebuildIndex() re-evaluates usage based on last requests.

/*
* Some alternate to consider
To prevent thrashing, I can implement a soft limit, say of 50 symbols and hard limit of (soft + 50 )

so we keep buffer of 50 symbols incase of spike, otherwise for 1000 symbols, if we get 1005,
then it will continuously evict a symbol and cause chaos.
if hard-limit reached, stop adding new symbols. The only fail-safe

*/