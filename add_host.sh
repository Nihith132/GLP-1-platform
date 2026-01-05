#!/bin/bash
# Add Supabase host to /etc/hosts
echo ""
echo "This will add the Supabase database hostname to your /etc/hosts file"
echo "You'll need to enter your Mac password when prompted"
echo ""
echo "2406:da18:1b2:3601:6ce:cff8:2b8a:8f3 db.ydslktnlmxgryngjzast.supabase.co" | sudo tee -a /etc/hosts
