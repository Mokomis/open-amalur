# Read-only queries through the parent's already-running Windows REA session.
Set-Location 'C:\Users\rwill\Documents\Opem Amalur'
@{label='audit_ability_names';tool='search_strings';arguments=@{pattern='^(ability|player_ability)$|AbilityMgr|PlayerAbility';mode='regex';case_sensitive=$false}} | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 work\scene-v08-requests\020-audit-ability-names.json
@{label='audit_ability_rtti_refs';tool='xrefs';arguments=@{address='0x0196bf48'}} | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 work\scene-v08-requests\021-audit-ability-rtti-refs.json
# aa7bd0 pseudocode is already retained; assembly resolves hidden ECX manager
# selection and whether its category parameter chooses a specific manager.
@{label='audit_asset_macro_assembly';tool='procedure_assembly';arguments=@{procedure='0x00aa7bd0'}} | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 work\scene-v08-requests\022-audit-asset-macro-assembly.json
