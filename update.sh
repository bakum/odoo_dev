#!/usr/bin/env bash
# npm install
echo 'Update script for OptimusAgro Trade'
PS3='Choose your update option: '
options=("Git" "GitWithStash" "GitResetHard" "Quit")
select fav in "${options[@]}"; do
    case $fav in
        "Git")
            echo "Update from $fav over pull command!"
	          git pull origin 16.0
            ;;
        "GitWithStash")
            echo "Update from $fav over pull command with stash!"
	          git stash
	          git pull origin 16.0
	          git stash apply --index
            ;;
        "GitResetHard")
            echo "Git reset hard"
	          git reset --hard
            ;;
	      "Quit")
	          echo "User requested exit"
	          exit
	          ;;
          *) echo "invalid option $REPLY";;
    esac
done
