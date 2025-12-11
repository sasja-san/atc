

# SDK version 

After running `dsd rom extract`, in `extract/arm9/arm9.yaml`
there's a line `sdk_version: 67269937`

```{.txt}
67269937 == 0x04_02_7531
  0x7531 == 30001
```

Which gives us

  * Major version: 4
  * Minor version: 2
  * Patch version: 30001









# Game Logic

## Airport codes

  1. rjff / Fukuoka Airport
  2. rjbb / Kansai International Airport
  3. rjgg / Chubu Centrair International Airport
  4. rjtt / Haneda Airport
  5. rjcc / New Chitose Airport







### RJFF / Fukuoka

  * Rookie -  700 - 09:30 ~ 11:00
  * Novice - 2300 - 13:00 ~ 15:00
  * Expert - 5900 - 16:00 ~ 19:00

### RJBB / Kansai Intl

  * Rookie - 1500 - 08:15 ~ 10:00
  * Novice - 2800 - 13:00 ~ 15:00
  * Expert - 6200 - 20:00 ~ 23:00

### RJGG / Chubu Intl

  * Rookie - 1600 - 09:00 ~ 11:00
  * Novice - 3200 - 14:00 ~ 16:00
  * Expert - 6000 - 11:30 ~ 14:00

### RJTT / Tokyo Intl

  * Rookie - 1600 - 11:00 ~ 13:00
  * Novice - 3300 - 13:00 ~ 15:00
  * Expert - 4800 - 11:30 ~ 14:00

### RJCC / New Chitose

  * Rookie - 1900 - 13:00 ~ 15:00
  * Novice - 4000 - 11:45 ~ 14:00
  * Expert - 3400 - 12:00 ~ 14:00





# Airport directory contents 

RJFF as example

NCLR: Nitro CoLoR
NCBR: Nitro BackgRound ???
NCER: Nitro CEll Resource

## Graphics

  * rjff_00.NCLR [stage background palette]
  * rjff_00.NCBR [stage background]

  * com_rjff.NANR [menu choices]
  * com_rjff.NCER [menu choices]
  * com_rjff.NCGR [menu choices]

  * icon_rjff.NCBR [stage numbers]
  * icon_rjff.NCER [stage numbers]
  * icon_rjff.NCGR [stage numbers]

## .dat files

  * approach_rjff_1.dat [radio message texts]
  * imgname_rjff_1.dat [$var <--> plane sprite name]
  * selectname_rjff_1.dat [$var <--> binary]

  * traffic_rjff_1.dat [level script] 
  * traffic_rjff_2.dat [level script]
  * traffic_rjff_3.dat [level script]

  * link_rjff_1.dat [binary]
  * point_rjff_1.dat [binary]
  * select_rjff_1.dat [binary]
  * stage_rjff_1.dat [binary]
  * taglink_rjff_1.dat [binary]
  * trafinit_rjff_1.dat [binary]


# Plane directory


