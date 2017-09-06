# Set terminal colors to match system theme
# setsid wal -r 

# # Enable Gnome keyring for ssh
if [ -n "$DESKTOP_SESSION" ]
    gnome-keyring-daemon --start > /dev/null
    export SSH_AUTH_SOCK
end
