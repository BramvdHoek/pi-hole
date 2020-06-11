import subprocess, commands, requests, json, collections, time
from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime
from font_source_sans_pro import SourceSansPro, SourceSansProBold

#--------------------------------- Functions ----------------------------------#
def getTenMinuteData(pihole_ip):
    # Get the data that is collected every 10 minute by the overTimeData10mins

    # Get data from the pihole api, convert ordered json format
    data_source = 'http://'+ pihole_ip +'/admin/api.php?overTimeData10mins'
    rawdata = requests.get(data_source)
    ordered_json = json.loads(rawdata.text, object_pairs_hook = collections.OrderedDict)

    # for-loop into ordered_json, convert UNIX value to timestamp
    # looking up 'domains_over_time', 'ads_over_time' is also available

    for key, value in ordered_json['domains_over_time'].items():
        key = float(key)
        converted_key = datetime.fromtimestamp(key).strftime('%d-%m-%Y %H:%M')
        #print("Time: " + converted_key + " Count: " + str(value))

#----------------------------- Settings change me -----------------------------#
#ipadress of the pihole server
pihole_ip = "192.168.1.4"

#------------------------------ Start Main Code -------------------------------#
inky_display = InkyPHAT(colour="black")
inky_display.set_border(inky_display.WHITE)
img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))

color = inky_display.BLACK
font = ImageFont.truetype(SourceSansPro, 12)
font_bold = ImageFont.truetype(SourceSansProBold, 12)
max_width = inky_display.HEIGHT
max_height = inky_display.WIDTH
h_line = 14

# 1bit mask canvas to fit the text (rotated 90deg before pasted on 'img' Image)
mask = Image.new("1", (inky_display.HEIGHT, inky_display.WIDTH))

# Stats to display on screen
host = subprocess.check_output("hostname", shell=True).strip() + ".local"
ip = subprocess.check_output( "hostname -I | cut -d' ' -f1", shell=True).strip()
mem_usage = subprocess.check_output("free -m | awk 'NR==2{printf \"%s/%sMB %.0f%%\", $3,$2,$3*100/$2 }'", shell=True).strip()
disk = subprocess.check_output("df -h | awk '$NF==\"/\"{printf \"%d/%dGB %s\", $3,$2,$5}'", shell=True).strip()
temp = commands.getstatusoutput("vcgencmd measure_temp")[1].replace("temp=", "").replace("'", "\xb0")

# Dimensions of stats text
w_host, h_host = font.getsize(host)
w_ip, h_ip = font.getsize(ip)
w_mem, h_mem = font.getsize(mem_usage)
w_disk, h_disk = font.getsize(disk)
w_temp, h_temp = font.getsize(temp)

# Set up mask ImageDraw
mask_draw = ImageDraw.Draw(mask)

# Write the text on the mask, using colour 1 (on) as this is an on/off 1bit canvas
# System info
mask_draw.text((0, 0), "Host: ", 1, font_bold)
mask_draw.text((max_width-w_host-2, 0), host, 1, font)
mask_draw.text((0, h_line), "IP: ", 1, font_bold)
mask_draw.text((max_width-w_ip, 15), ip, 1, font)
mask_draw.text((0, h_line*2), "Mem: ", 1, font_bold)
mask_draw.text((max_width-w_mem, h_line*2), mem_usage, 1, font)
mask_draw.text((0, h_line*3), "Disk: ", 1, font_bold)
mask_draw.text((max_width-w_disk, h_line*3), disk, 1, font)
mask_draw.text((0, h_line*4), "Temp: ", 1, font_bold)
mask_draw.text((max_width-w_temp, h_line*4), temp, 1, font)
mask_draw.line([(0, h_line*5+2), (max_width, h_line*5+2)], fill=color, width=2)

#Pi-hole stats
rawdata = requests.get("http://" + pihole_ip + "/admin/api.php?summary").json()
clients = rawdata["unique_clients"]
dns_queries = rawdata["dns_queries_all_types"]
ads_percentage = rawdata["ads_percentage_today"]
blocked = ads_percentage + " %"

stats_title = "Daily Pi-Hole Stats"
w_title, h_title = font.getsize(stats_title)
w_clients, h_clients = font.getsize(clients)
w_queries, h_queries = font.getsize(dns_queries)
w_blocked, h_blocked = font.getsize(blocked)
start_h = h_line*5+4

mask_draw.text(((max_width-w_title)/2, start_h), stats_title, 1, font_bold)
mask_draw.text((0, start_h+h_line), "Clients: ", 1, font_bold)
mask_draw.text((max_width-w_clients, start_h+15), clients, 1, font)
mask_draw.text((0, start_h+h_line*2), "Queries: ", 1, font_bold)
mask_draw.text((max_width-w_queries, start_h+h_line*2), dns_queries, 1, font)
mask_draw.text((0, start_h+h_line*3), "Blocked: ", 1, font_bold)
mask_draw.text((max_width-w_blocked, start_h+h_line*3), blocked, 1, font)

getTenMinuteData(pihole_ip)

graph_start = start_h+h_line*4+2

graph_img = Image.new("1", (inky_display.HEIGHT, inky_display.WIDTH - graph_start))
graph_draw =ImageDraw.Draw(graph_img)
graph_draw.rectangle([ (0,0), (inky_display.HEIGHT-1, inky_display.width - graph_start-1) ], fill=None, outline=color)



# Rotate the mask Image so everything is displayed vertically
mask = mask.rotate(90, expand=True)
# Put the mask on the main Image
img.paste(color, (0,0), mask)

graph_img = graph_img.rotate(90, expand=True)
img.paste(color, (graph_start,0), graph_img)

draw = ImageDraw.Draw(img)
inky_display.set_image(img)
inky_display.show()
