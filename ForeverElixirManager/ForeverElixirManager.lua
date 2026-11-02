-- ForeverElixirManager v0.1.0
-- Queue a single available elixir; use only through a manual secure click.
local PREFIX = "|cff8bcaff[ElixirManager]|r "
local elixirs = {
    { id = 2458, name = "Elixir of Minor Fortitude" },
    { id = 250330, name = "Minor Cleric's Elixir" },
    { id = 250339, name = "Minor Mageblood Elixir" },
    { id = 250344, name = "Elixir of Minor Spirit" },
    { id = 3383, name = "Elixir of Wisdom" },
    { id = 3389, name = "Elixir of Lesser Defense" },
}
-- TODO: Verify Forever-specific aura names against the in-game buff list.
local button = CreateFrame("Button", "ForeverElixirSecureBtn", UIParent, "SecureActionButtonTemplate")
button:SetSize(1, 1)
button:SetPoint("TOPLEFT", UIParent, "TOPLEFT", -10, 10)
button:SetAlpha(0)
button:RegisterForClicks("AnyUp")
local frame = CreateFrame("Frame")
local queuedID, lastMessage
local settings
local function report(message)
    if lastMessage ~= message then
        print(PREFIX .. message)
        lastMessage = message
    end
end
local function buffs()
    local active = {}
    if C_UnitAuras and C_UnitAuras.GetAuraDataByIndex then
        for i = 1, 255 do
            local aura = C_UnitAuras.GetAuraDataByIndex("player", i, "HELPFUL")
            if not aura then break end
            if aura.name then active[aura.name] = true end
        end
    elseif UnitBuff then
        for i = 1, 255 do
            local name = UnitBuff("player", i)
            if not name then break end
            active[name] = true
        end
    end
    return active
end
local function update()
    if InCombatLockdown() then return end
    local active, selected, missing = buffs(), nil, false
    for _, e in ipairs(elixirs) do
        if settings[e.id] ~= false and not active[e.name] then
            missing = true
            if GetItemCount(e.id, false) > 0 then selected = e; break end
        end
    end
    if selected then
        if queuedID ~= selected.id then
            button:SetAttribute("type", "item")
            button:SetAttribute("item", "item:" .. selected.id)
            queuedID = selected.id
            report("Next up: " .. selected.name)
        end
    else
        button:SetAttribute("type", nil)
        button:SetAttribute("item", nil)
        queuedID = nil
        report(missing and "No missing elixirs available in bags." or "All tracked buffs active.")
    end
end
frame:RegisterEvent("PLAYER_LOGIN")
frame:RegisterEvent("PLAYER_REGEN_ENABLED")
frame:RegisterEvent("BAG_UPDATE")
frame:RegisterEvent("UNIT_AURA")
frame:SetScript("OnEvent", function(_, event, unit)
    if event == "PLAYER_LOGIN" then
        ForeverElixirManagerDB = ForeverElixirManagerDB or {}
        settings = ForeverElixirManagerDB
    end
    if event == "UNIT_AURA" and unit ~= "player" then return end
    update()
end)
SLASH_FOREVERELIXIR1 = "/fem"
SlashCmdList.FOREVERELIXIR = function(arg)
    arg = (arg or ""):lower()
    local command, number = arg:match("^(%S+)%s+(%d+)$")
    number = tonumber(number)
    if (command == "enable" or command == "disable") and number and elixirs[number] then
        if InCombatLockdown() then print(PREFIX .. "Configuration unavailable in combat."); return end
        settings[elixirs[number].id] = command == "enable"
        lastMessage = nil
        update()
        print(PREFIX .. elixirs[number].name .. " " .. (command == "enable" and "enabled" or "disabled"))
    elseif arg == "list" then
        for i, e in ipairs(elixirs) do
            print(PREFIX .. i .. ". " .. e.name .. " [" .. (settings[e.id] == false and "OFF" or "ON") .. "]")
        end
    elseif arg == "buffs" then
        local active = buffs()
        for _, e in ipairs(elixirs) do
            print(PREFIX .. e.name .. ": " .. (active[e.name] and "ACTIVE" or "MISSING") ..
                ", bags=" .. GetItemCount(e.id, false))
        end
    elseif arg == "status" then
        print(PREFIX .. (queuedID and ("Queued item ID: " .. queuedID) or "No item queued"))
    else
        update()
        print(PREFIX .. "Commands: /fem list, /fem enable N, /fem disable N, /fem buffs, /fem status")
    end
end
