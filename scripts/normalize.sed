s/\r$//
s/^[[:space:]]+//
s/[[:space:]]+$//
s/[[:space:]]*,[[:space:]]*/,/g
s/No Info/no_info/g
s/no info/no_info/g
s/No info/no_info/g
s/,/	/g
