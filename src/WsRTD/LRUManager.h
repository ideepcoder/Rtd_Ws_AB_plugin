/*/////////
*	Author: ideepcoder
*	Date: 20251212
*	LRUManager.h
*	Build Least Recently Used ticker/symbol for evict_when_map_full in pro features.
*///////////

// LRUManager.cpp
// 
#pragma once

#include "stdafx.h"
#include <map>
#include <set>
#include "Plugin.h"

// These are the only quickest ways to compare QEX and old date stored, to update LRU Index
constexpr uint64_t MASK_YMDH = 0xFFFFFFE000000000ULL;

constexpr uint64_t MASK_8MIN = 0xFFFFFFFFF8000000ULL; // in use

// map alias used by LRUManager
typedef std::map<CString, Ticker*> TickerMap;

// ---------- LRU index structures ----------
struct LRUEntry {
    uint64_t date;   // raw 64-bit date: smaller => older (evict first)
    CString key;     // symbol
};

// comparator: sort by date ascending, tie-break by key to keep deterministic order
struct LRUEntryCmp {
    bool operator()( LRUEntry const& a, LRUEntry const& b ) const;
};

class LRUManager {

private:

    const TickerMap& m_mapSym;

    // main index: sorted by (date, key)
    std::set<LRUEntry, LRUEntryCmp> m_index;

    // lookup: key -> iterator to entry in m_index for quick update/removal
    std::map<CString, std::set<LRUEntry, LRUEntryCmp>::iterator> m_lookup;

public:
    // ctor takes reference to underlying map so it can extract Date values when building/updating
    explicit LRUManager( TickerMap& mapSym );

    ~LRUManager();

    // Rebuild LRU index
    void RebuildIndex();

    // Called when Ticker has 'key' its IdxQEx changes, or added as new symbol.
    // If key is new it will be added.
    void AddOrUpdateKey( const CString& key, uint64_t newDate );

    // Remove key from index. called when symbol removed from MapSym
    void RemoveKey( const CString& key );

    // Returns true if we evicted at least one symbol. For each eviction, OnEvictSymbol(key) is called.
    // Evicts until MapSym.size() <= maxSize.
    int EvictIfOverLimit( size_t maxSize );

    // Debug helper: print LRU index (optional)
    void DebugPrintIndex() const;


private:
    // Helper: safely extract the 64-bit date for a given symbol key in the map.
    // If ticker missing, pRtQtarr missing, or IdxQEx == -1, returns 0 (smallest) so it becomes highest-priority deletable.
    uint64_t ExtractDateForKey( const CString& key ) const;

    // insert entry into set and store iterator in lookup
    void InsertEntry( const CString& key, uint64_t date );
};
