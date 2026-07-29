# bash completion for biologis-cogitator / cogitator / init-cogitator
_biologis_cogitator() {
  local cur prev
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD - 1]}"

  local cmds="wizard setup packs generate-system generate show propose-export layers help"

  if [[ ${COMP_CWORD} -eq 1 ]]; then
    COMPREPLY=($(compgen -W "${cmds}" -- "${cur}"))
    return 0
  fi

  case "${COMP_WORDS[1]}" in
    wizard)
      COMPREPLY=($(compgen -W "--seed --pack" -- "${cur}"))
      ;;
    generate-system)
      COMPREPLY=($(compgen -W "--seed --spark --mode --existing --pack" -- "${cur}"))
      ;;
    generate)
      COMPREPLY=($(compgen -W "--seed --spark --from-lock --system --existing-system --pack" -- "${cur}"))
      ;;
    show)
      COMPREPLY=($(compgen -W "--json --as-system" -- "${cur}"))
      ;;
    *)
      ;;
  esac
  return 0
}

complete -F _biologis_cogitator biologis-cogitator
complete -F _biologis_cogitator cogitator
complete -F _biologis_cogitator init-cogitator
