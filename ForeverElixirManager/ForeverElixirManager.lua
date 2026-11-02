-- Copyright (c) 2026 Martin Gammelgård Rasmussen. MIT; see packaged LICENSE.
-- Candidate IDs only. Aura mappings must be observed on the Forever client.
local PREFIX = "|cff8bcaff[ElixirManager]|r "
local elixirs = {
    { id = 2458, name = "Elixir of Minor Fortitude" },
    { id = 250330, name = "Minor Cleric's Elixir" },
    { id = 250339, name = "Minor Mageblood Elixir" },
    { id = 250344, name = "Elixir of Minor Spirit" },
    { id = 3383, name = "Elixir of Wisdom" },
    { id = 3389, name = "Elixir of Lesser Defense" },
}
local byID = {}
for _, entry in ipairs(elixirs) do byID[entry.id] = entry end
local frame = CreateFrame("Frame")
local button, settings, queuedID, lastMessage, startupError
local reasons, pendingItems = {}, {}
local function say(message) print(PREFIX .. message) end
local function report(message)
    if message ~= lastMessage then say(message); lastMessage = message end
end
local function readable(value)
    return not issecretvalue or not issecretvalue(value)
end
local function integer(value, minimum)
    return readable(value) and type(value) == "number" and value < math.huge
        and value >= minimum and value == math.floor(value)
end
local function locked()
    return type(InCombatLockdown) ~= "function" or InCombatLockdown()
end
local function defaults(old)
    local result = { order = {}, enabled = {}, auras = {}, blockers = {} }
    for _, e in ipairs(elixirs) do
        result.order[#result.order + 1] = e.id
        result.enabled[e.id] = type(old) ~= "table" or old[e.id] ~= false
    end
    return result
end
local function normalize(db)
    if type(db) ~= "table" then return defaults(ForeverElixirManagerDB) end
    local clean, seen = defaults(), {}
    clean.order = {}
    if type(db.order) == "table" then
        for _, id in ipairs(db.order) do
            if byID[id] and not seen[id] then
                seen[id] = true; clean.order[#clean.order + 1] = id
            end
        end
    end
    for _, e in ipairs(elixirs) do
        if not seen[e.id] then clean.order[#clean.order + 1] = e.id end
        clean.enabled[e.id] = type(db.enabled) ~= "table" or db.enabled[e.id] ~= false
        if type(db.auras) == "table" and integer(db.auras[e.id], 1) then
            clean.auras[e.id] = db.auras[e.id]
        end
        clean.blockers[e.id] = {}
        local blockers = type(db.blockers) == "table" and db.blockers[e.id]
        if type(blockers) == "table" then
            for id, enabled in pairs(blockers) do
                if integer(id, 1) and enabled == true then clean.blockers[e.id][id] = true end
            end
        end
    end
    return clean
end
local function activeAuras()
    if not C_UnitAuras or type(C_UnitAuras.GetAuraDataByIndex) ~= "function" then
        return nil, "Aura API unavailable; selection stopped."
    end
    local active, entries = {}, {}
    for i = 1, 255 do
        local aura = C_UnitAuras.GetAuraDataByIndex("player", i, "HELPFUL")
        if not readable(aura) then return nil, "Restricted aura data; selection stopped." end
        if aura == nil then return active, entries end
        if type(aura) ~= "table" or not integer(aura.spellId, 1) then
            return nil, "Unreadable aura ID; selection stopped."
        end
        active[aura.spellId] = true
        entries[#entries + 1] = aura
    end
    return nil, "Aura scan limit reached; selection stopped."
end
local function candidate(id, level, active)
    if not settings.enabled[id] then return "disabled" end
    local auraID = settings.auras[id]
    if not auraID then return "aura mapping NOT VERIFIED (/fem aura N SPELLID)" end
    if active[auraID] then return "already active" end
    for blocker in pairs(settings.blockers[id] or {}) do
        if active[blocker] then return "conflicting effect active: " .. blocker end
    end
    local count = C_Item.GetItemCount(id, false, false, false, false)
    if not integer(count, 0) then return "invalid inventory response" end
    if count == 0 then return "not in bags" end
    if pendingItems[id] == "failed" then return "item data request failed; reload to retry" end
    local name, _, _, _, minimum = C_Item.GetItemInfo(id)
    if not readable(name) or type(name) ~= "string" or not integer(minimum, 0) then
        if not pendingItems[id] and type(C_Item.RequestLoadItemDataByID) == "function" then
            pendingItems[id] = true
            C_Item.RequestLoadItemDataByID(id)
        end
        return "item data unavailable (or invalid item ID)"
    end
    if level < minimum then return "requires level " .. minimum end
    if not C_Spell or type(C_Spell.GetSpellInfo) ~= "function" then return "Spell API unavailable" end
    local spell = C_Spell.GetSpellInfo(auraID)
    if not readable(spell) or type(spell) ~= "table" or not integer(spell.spellID, 1)
        or spell.spellID ~= auraID then return "aura spell data unavailable (or invalid ID)" end
    return "eligible", name
end
local function selectItem()
    if not C_Item or type(C_Item.GetItemCount) ~= "function" or type(C_Item.GetItemInfo) ~= "function"
        or type(UnitLevel) ~= "function" then return nil, "Required item/level API unavailable." end
    local level = UnitLevel("player")
    if not integer(level, 1) then return nil, "Player level unavailable." end
    local active, detail = activeAuras()
    if not active then return nil, detail end
    local selected, selectedName
    for _, id in ipairs(settings.order) do
        local reason, name = candidate(id, level, active)
        reasons[id] = reason
        if reason == "eligible" and not selected then selected, selectedName = id, name end
    end
    return selected, selected and ("Next up: " .. selectedName) or "No eligible elixir; /fem list explains why."
end
local function applySelection(id)
    if queuedID == id then return end
    -- Disable before changing the target. Item IDs survive bag-slot moves.
    button:SetAttribute("type", nil)
    button:SetAttribute("item", id and ("item:" .. id) or nil)
    button:SetAttribute("queuedType", id and "item" or nil)
    button:SetAttribute("type", id and "item" or nil)
    queuedID = id
end
local function update()
    if not settings then return end
    if startupError then report(startupError); return end
    if not button then return end
    if locked() then return end -- No aura/inventory decisions in combat.
    reasons = {}
    local ok, id, message = pcall(selectItem)
    if not ok then id, message = nil, "Client API error; selection stopped. Use /fem status." end
    applySelection(id)
    report(message)
end
local function initializeButton()
    if type(InCombatLockdown) ~= "function" then
        startupError = "Combat API unavailable; manual queue disabled."
        return
    end
    if locked() then return end
    if type(RegisterStateDriver) ~= "function" then
        startupError = "Secure state API unavailable; manual queue disabled."
        return
    end
    button = CreateFrame("Button", "ForeverElixirSecureBtn", UIParent,
        "SecureActionButtonTemplate,SecureHandlerStateTemplate")
    button:SetSize(1, 1)
    button:SetPoint("TOPLEFT", UIParent, "TOPLEFT", -10, 10)
    button:SetAlpha(0)
    button:RegisterForClicks("AnyUp")
    button:SetAttribute("useOnKeyDown", false)
    -- Fixed combat condition only: no item selection or combat decisions here.
    button:SetAttribute("_onstate-combat", [[
        if newstate == "combat" then
            self:SetAttribute("type", nil)
        else
            self:SetAttribute("type", self:GetAttribute("queuedType"))
        end
    ]])
    RegisterStateDriver(button, "combat", "[combat] combat; safe")
end
local function initialize()
    if not settings then
        settings = normalize(ForeverElixirManagerCharDB)
        ForeverElixirManagerCharDB = settings
    end
    if not button and not startupError then
        local ok = pcall(initializeButton)
        if not ok then startupError = "Secure button setup failed; reload after checking client support." end
    end
    if button or startupError then update() end
end
local function schedule()
    if not settings or locked() or frame:GetScript("OnUpdate") then return end
    -- One next-frame refresh per event burst; no permanent polling.
    frame:SetScript("OnUpdate", function(self)
        self:SetScript("OnUpdate", nil)
        update()
    end)
end
frame:SetScript("OnEvent", function(_, event, unit, success)
    if event == "PLAYER_LOGIN" or event == "PLAYER_REGEN_ENABLED" then initialize(); return end
    if event == "UNIT_AURA" and unit ~= "player" then return end
    if event == "GET_ITEM_INFO_RECEIVED" then
        if not pendingItems[unit] then return end
        if success == false then pendingItems[unit] = "failed"
        elseif success == true then pendingItems[unit] = true end
    end
    schedule()
end)
for _, event in ipairs({ "PLAYER_LOGIN", "PLAYER_REGEN_ENABLED", "PLAYER_ENTERING_WORLD",
    "BAG_UPDATE", "UNIT_AURA", "PLAYER_LEVEL_UP", "GET_ITEM_INFO_RECEIVED" }) do
    local ok = pcall(frame.RegisterEvent, frame, event)
    if not ok then startupError = "Required event unavailable: " .. event .. "; selection stopped." end
end
SLASH_FOREVERELIXIR1 = "/fem"
SlashCmdList.FOREVERELIXIR = function(arg)
    if not settings then say("Waiting for player login."); return end
    local command, first, second = (arg or ""):lower():match("^%s*(%S*)%s*(%S*)%s*(.-)%s*$")
    local n, value = tonumber(first), tonumber(second)
    local id = n and settings.order[n]
    if command == "status" then
        if locked() then say("Combat: selection paused; secure item action disabled.")
        else update(); say(lastMessage or "No item queued.") end
    elseif command == "list" then
        update()
        for index, itemID in ipairs(settings.order) do
            local blockers = {}
            for spellID in pairs(settings.blockers[itemID] or {}) do blockers[#blockers + 1] = spellID end
            table.sort(blockers)
            for i, spellID in ipairs(blockers) do blockers[i] = tostring(spellID) end
            say(index .. ". " .. byID[itemID].name .. " (" .. itemID .. ") ["
                .. (settings.enabled[itemID] and "ON" or "OFF") .. "] aura="
                .. (settings.auras[itemID] or "NOT VERIFIED") .. " blockers="
                .. (#blockers > 0 and table.concat(blockers, ",") or "none")
                .. ": " .. (locked() and "paused in combat" or reasons[itemID] or "not evaluated"))
        end
    elseif command == "buffs" then
        if locked() then say("Aura inspection unavailable in combat."); return end
        local ok, active, entries = pcall(activeAuras)
        if not ok or not active then say("Aura data unavailable."); return end
        for _, aura in ipairs(entries) do
            local name = readable(aura.name) and type(aura.name) == "string" and aura.name or "unnamed"
            say(aura.spellId .. ": " .. name)
        end
        if #entries == 0 then say("No helpful auras.") end
    elseif command == "reset" or command == "enable" or command == "disable" or command == "move"
        or command == "aura" or command == "block" or command == "unblock" then
        if locked() then say("Configuration unavailable in combat."); return end
        if command == "reset" and first == "" then
            settings = defaults(); ForeverElixirManagerCharDB = settings
        elseif not id then say("Invalid priority number; use /fem list."); return
        elseif (command == "enable" or command == "disable") and second == "" then
            settings.enabled[id] = command == "enable"
        elseif command == "move" and integer(value, 1) and value <= #settings.order then
            table.remove(settings.order, n); table.insert(settings.order, value, id)
        elseif command == "aura" and integer(value, 0) then
            settings.auras[id] = value > 0 and value or nil
            say("User-supplied aura mapping saved; verify stacking before manual use.")
        elseif (command == "block" or command == "unblock") and integer(value, 1) then
            settings.blockers[id] = settings.blockers[id] or {}
            settings.blockers[id][value] = command == "block" or nil
        else say("Invalid arguments; use /fem help."); return end
        update()
        say("Configuration saved for this character.")
    else
        update()
        say("Commands: list, status, buffs, enable N, disable N, move N POSITION, aura N SPELLID (0 clears), block N SPELLID, unblock N SPELLID, reset")
    end
end
