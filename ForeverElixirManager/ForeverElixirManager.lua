-- Copyright (c) 2026 Martin Gammelgård Rasmussen. MIT; see packaged LICENSE.
-- Forever API evidence and buff-name assumptions: docs/ELIXIR_RANKS.md.
local PREFIX = "|cff8bcaff[ElixirManager]|r "
local elixirs = {
    -- Group IDs preserve existing saved toggles. Ranks are strongest first.
    { id = 2458, name = "Fortitude", ranks = {
        { id = 250335, name = "Elixir of Greater Fortitude", strength = 400 },
        { id = 250334, name = "Elixir of Fortitude", strength = 200 },
        { id = 3825, name = "Elixir of Lesser Fortitude", strength = 120 },
        { id = 2458, name = "Elixir of Minor Fortitude", strength = 27 },
    } },
    { id = 250330, name = "Cleric's", ranks = {
        { id = 250333, name = "Greater Cleric's Elixir", strength = 40 },
        { id = 250332, name = "Cleric's Elixir", strength = 30 },
        { id = 250331, name = "Lesser Cleric's Elixir", strength = 20 },
        { id = 250330, name = "Minor Cleric's Elixir", strength = 10 },
    } },
    { id = 250339, name = "Mageblood", ranks = {
        { id = 250341, name = "Greater Mageblood Elixir", strength = 20 },
        { id = 20007, name = "Mageblood Elixir", strength = 12 },
        { id = 250340, name = "Lesser Mageblood Elixir", strength = 6 },
        { id = 250339, name = "Minor Mageblood Elixir", strength = 3 },
    } },
    { id = 250344, name = "Spirit", ranks = {
        { id = 250347, name = "Elixir of Greater Spirit", strength = 18 },
        { id = 250346, name = "Elixir of Spirit", strength = 10 },
        { id = 250345, name = "Elixir of Lesser Spirit", strength = 6 },
        { id = 250344, name = "Elixir of Minor Spirit", strength = 3 },
    } },
    { id = 3383, name = "Intellect", ranks = {
        { id = 9179, name = "Elixir of Greater Intellect", strength = 25 },
        { id = 250354, name = "Elixir of Intellect", strength = 10 },
        -- Equal effect: prefer Wisdom's longer database duration, then Lesser.
        { id = 3383, name = "Elixir of Wisdom", strength = 6 },
        { id = 250353, name = "Elixir of Lesser Intellect", strength = 6 },
    } },
    { id = 3389, name = "Defense", ranks = {
        { id = 13445, name = "Elixir of Greater Defense", strength = 450 },
        { id = 8951, name = "Elixir of Defense", strength = 250 },
        { id = 3389, name = "Elixir of Lesser Defense", strength = 150 },
        { id = 5997, name = "Elixir of Minor Defense", strength = 50 },
    } },
    { id = "otherElixirs", name = "Other elixirs", ranks = {} },
    { id = "scrolls", name = "Scrolls", ranks = {} },
}
local rankedItems = {}
for _, group in ipairs(elixirs) do
    for _, entry in ipairs(group.ranks) do rankedItems[entry.id] = true end
end
local frame = CreateFrame("Frame")
local button, settings, queuedID, lastMessage, startupError
local pendingItems, carriedItems = {}, {}
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
local function activeAuras()
    if not C_UnitAuras or type(C_UnitAuras.GetAuraDataByIndex) ~= "function" then
        return nil, "Aura API unavailable; selection stopped."
    end
    local active = {}
    for i = 1, 255 do
        local aura = C_UnitAuras.GetAuraDataByIndex("player", i, "HELPFUL")
        if not readable(aura) then return nil, "Restricted aura data; selection stopped." end
        if aura == nil then return active end
        if type(aura) ~= "table" or not readable(aura.name) or type(aura.name) ~= "string"
            or aura.name == "" then
            return nil, "Unreadable buff name; selection stopped."
        end
        active[aura.name] = true
    end
    return nil, "Aura scan limit reached; selection stopped."
end
local function activeStrength(group, active)
    local strength = 0
    for _, entry in ipairs(group.ranks) do
        if active[entry.name] then strength = math.max(strength, entry.strength) end
    end
    return strength
end
local function requestItem(id)
    if not pendingItems[id] and type(C_Item.RequestLoadItemDataByID) == "function" then
        pendingItems[id] = true
        C_Item.RequestLoadItemDataByID(id)
    end
end
local function textValue(value)
    return readable(value) and type(value) == "string" and value ~= ""
end
local function discoverItems()
    carriedItems = {}
    if not C_Container or type(C_Container.GetContainerNumSlots) ~= "function"
        or type(C_Container.GetContainerItemID) ~= "function"
        or type(C_Item.GetItemSpell) ~= "function" or not integer(NUM_BAG_SLOTS, 0) then
        return "Bag discovery API unavailable; additional elixirs/scrolls not scanned."
    end
    local seen, incomplete = {}, false
    -- Backpack and equipped bags only. Never inspect bank containers.
    for bag = 0, NUM_BAG_SLOTS do
        local slots = C_Container.GetContainerNumSlots(bag)
        if not integer(slots, 0) then error("Unreadable bag size") end
        for slot = 1, slots do
            local id = C_Container.GetContainerItemID(bag, slot)
            if not readable(id) or (id ~= nil and not integer(id, 1)) then error("Unreadable bag item") end
            if id and not seen[id] and not rankedItems[id] then
                seen[id] = true
                if pendingItems[id] ~= "failed" then
                    local name, _, _, _, minimum, _, _, _, _, _, _, class, subclass = C_Item.GetItemInfo(id)
                    if not textValue(name) or not integer(minimum, 0)
                        or not integer(class, 0) or not integer(subclass, 0) then
                        requestItem(id)
                        incomplete = true
                    -- Forever UI enum: Consumable=0, Elixir=2, Scroll=4.
                    elseif class == 0 and (subclass == 2 or subclass == 4) then
                        local spell = C_Item.GetItemSpell(id)
                        if textValue(spell) then
                            carriedItems[#carriedItems + 1] = { id = id, name = name,
                                minimum = minimum, spell = spell,
                                group = subclass == 2 and "otherElixirs" or "scrolls" }
                        else
                            requestItem(id)
                            incomplete = true
                        end
                    end
                else
                    incomplete = true
                end
            end
        end
    end
    -- Stable order across bag moves. Unknown effects are not ranked by item level.
    table.sort(carriedItems, function(a, b) return a.id < b.id end)
    if incomplete then return "Some bag item data unavailable; discovery incomplete." end
end
local function discoveredActive(entry, active)
    -- Use-spell NAME is a testable heuristic, not proof of a matching aura ID.
    -- Any matching aura blocks reuse; do not infer an upgrade from item level.
    return active[entry.name] or active[entry.spell]
end
local function candidate(entry, level)
    local id = entry.id
    local count = C_Item.GetItemCount(id, false, false, false, false)
    if not integer(count, 1) or pendingItems[id] == "failed" then return end
    local name, _, _, _, minimum = C_Item.GetItemInfo(id)
    if not readable(name) or type(name) ~= "string" or not integer(minimum, 0) then
        requestItem(id)
        return
    end
    if level >= minimum then return name end
end
local function selectItem()
    if not C_Item or type(C_Item.GetItemCount) ~= "function" or type(C_Item.GetItemInfo) ~= "function"
        or type(UnitLevel) ~= "function" then return nil, "Required item/level API unavailable." end
    local level = UnitLevel("player")
    if not integer(level, 1) then return nil, "Player level unavailable." end
    local active, detail = activeAuras()
    if not active then return nil, detail end
    local discoveryWarning = discoverItems()
    for _, group in ipairs(elixirs) do
        if settings[group.id] ~= false then
            local strength = activeStrength(group, active)
            for _, entry in ipairs(group.ranks) do
                -- Never replace a recognized equal/stronger effect with a weaker one.
                if entry.strength > strength then
                    local name = candidate(entry, level)
                    if name then return entry.id, "Next up: " .. name end
                end
            end
            for _, entry in ipairs(carriedItems) do
                if entry.group == group.id and level >= entry.minimum
                    and not discoveredActive(entry, active) then
                    local name = candidate(entry, level)
                    if name then return entry.id, "Next up: " .. name end
                end
            end
        end
    end
    return nil, discoveryWarning or "No missing enabled elixir/scroll available for your level."
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
    button:SetAttribute("unit", "player") -- Scrolls must buff the player, not the current target.
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
        if type(ForeverElixirManagerCharDB) ~= "table" then ForeverElixirManagerCharDB = {} end
        local db = ForeverElixirManagerCharDB
        if type(db.enabled) ~= "table" then
            db.enabled = {}
            for _, entry in ipairs(elixirs) do
                db.enabled[entry.id] = type(ForeverElixirManagerDB) ~= "table"
                    or ForeverElixirManagerDB[entry.id] ~= false
            end
        end
        settings = db.enabled
        -- Old order/mappings/blockers are ignored but retained for rollback.
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
    arg = (arg or ""):lower():match("^%s*(.-)%s*$")
    local command, number = arg:match("^(%S+)%s+(%d+)$")
    local entry = elixirs[tonumber(number)]
    if arg == "status" then
        if locked() then say("Combat: selection paused; secure item action disabled.")
        else update(); say(lastMessage or "No item queued.") end
    elseif arg == "list" then
        for index, item in ipairs(elixirs) do
            say(index .. ". " .. item.name .. " [" .. (settings[item.id] == false and "OFF" or "ON") .. "]")
        end
        if not locked() then update() end
        for _, item in ipairs(carriedItems) do
            say(item.name .. " (item " .. item.id .. ", " .. item.group .. ")")
        end
    elseif arg == "buffs" then
        if locked() then say("Aura inspection unavailable in combat."); return end
        local ok, active = pcall(activeAuras)
        if not ok or not active then say("Aura data unavailable."); return end
        for _, item in ipairs(elixirs) do
            if #item.ranks > 0 then
                say(item.name .. ": " .. (activeStrength(item, active) > 0 and "ACTIVE" or "MISSING"))
            end
        end
        local discovered, warning = pcall(discoverItems)
        if not discovered then say("Bag data unavailable."); return end
        if warning then say(warning) end
        for _, item in ipairs(carriedItems) do
            say(item.name .. ": " .. (discoveredActive(item, active) and "ACTIVE" or "MISSING")
                .. " (assumed buff: " .. item.spell .. ")")
        end
    elseif (command == "enable" or command == "disable") and entry then
        if locked() then say("Configuration unavailable in combat."); return end
        settings[entry.id] = command == "enable"
        update()
        say(entry.name .. (command == "enable" and " enabled." or " disabled."))
    else
        update()
        say("Commands: /fem list, /fem enable N, /fem disable N, /fem buffs, /fem status")
    end
end
