from datetime import timedelta

permissions_for_clan = {
    "Head": [
        "invite_users",
        "kick_users",
        "edit_clan_settings",
        "assigning_roles",
        "delete_clan",
        "access_to_god_chat",
        "bank_access",
        "start_clan_wars",
        "moderate_chat",
    ],
    "Deputy": [
        "invite_users",
        "kick_users",
        "assigning_roles_to_elder",
        "delete_clan",
        "access_to_god_chat",
        "bank_access",
        "start_clan_wars",
        "moderate_chat",
    ],
    "Elder": [
        "invite_users",
        "kick_users",
        "moderate_chat",
    ],
    "Officer": ["invite_users"],
    "Participant": [],
}

max_of_clan_members_from_rang = {1: 25, 2: 30, 3: 35, 4: 40}

energy = {
    "energy_min": 0,
    "energy_max": 100
}
energy_per_battle = {1: 10}
time_add_one_energy = timedelta(seconds=5)
energy_per_time = {time_add_one_energy: 1}


