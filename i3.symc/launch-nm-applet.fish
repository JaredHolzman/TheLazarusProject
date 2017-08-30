#!/bin/fish
# launch-nm-applet.fish

# Hack to fix nm-applet loading icon error
function delay_load
    sleep 2s
    exec nm-applet
end

delay_load
