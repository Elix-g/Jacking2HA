# Jacking2HA


## Kurzbeschreibung
Auf der Suche nach Alternativen zur Homematic IP Integration für Home Assistant, bin ich auf die Möglichkeit gestoßen, meine CCU3-Zentrale per MQTT an Home Assistant anzubinden. Als Voraussetzung muss lediglich [CCU-Jack](https://github.com/mdzio/ccu-jack) als Add-On auf der Homematic-Zentrale laufen.
Jacking2HA ist ein kleines Tool, um die MQTT Topics des CCU-Jack in Home Assistant bekannt zu machen. Dabei bestehen die Möglichkeiten, die Topics per MQTT Auto Discovery bekannt zu machen oder die Informationen in eine gebrauchsfertige yaml-Datei zu schreiben die dann in die Home Assistant Konfiguration eingebunden werden kann.

## Funktionsweise
Nach dem Start wird Verbindung mit dem CCU-Jack VEAP-Server aufgenommen, um die Homematic-Geräte der Zentrale und deren Datenpunkte abzufragen. Wahlweise werden auch Systemvariablen, Zentralenprogramme und die virtuellen Geräte des CCU-Jacks zur weiteren Verarbeitung abgefragt. Im Anschluss werden die gefundenen Datenpunkte analysiert und versucht, dazu passende Home Assistant Entitätstypen zu finden. Dabei sind die Eigenschaften der Datenpunkte wie z.B. Typ und Name grundlegend. Als Name der Home Assistant Entitäten wird der Name des Datenpunkts gesetzt. Somit ist Jacking2HA prinzipiell für alle Homematic(-IP)-Geräte geeignet und nicht auf bestimmte Modelle beschränkt. Leider lässt sich nur aufgrund der Eigenschaften der Datenpunkte in einigen Fällen nicht immer der richtige Entitätstyp finden. Dennoch würde an dieser Stelle eine funktionierende Konfiguration der Autodiscover Topics bzw. eine funktionierende yamlk-Konfiguration erstellt werden können. Um Einfluss auf das Gesamtzergebnis zu nehmen, besteht zum einen die Möglichkeit, über eine Positivliste die Erkennung der Datenpunkte auf bestimmte Punkte und Kanäle zu beschränken. Dies ist besonders dann hilfreich, wenn ein Homematic-Gerät gleichnamige Datenpunkte in verschiedenen Kanälen liefert. Zum anderen können nach der Erkennung Anpassungen angewendet werden um das Gesamtergebnis zu verfeinern und zu korrigieren. Anpassungen können vorgenommen werden pauschal für Datenpunkte unabhängig von Kanal und Gerät oder gezielt für bestimmte Datenpunkte bestimmter Geräte und bestimmter Kanäle und allem dazwischen. Anpassungen können jegliche Entitätseigenschaften angegeben werden, die von der Home Assistant MQTT Integration für Auto Discovery erlaubt sind. Anpassungen überschreiben grundsätzlich bereits vorhandene Eigenschaften und da Jacking2HA Anpassungen nicht weiter prüft, kann es passieren, dass Anpassungen zu Fehlern im Gesamtergebnis führen. Jacking2HA kann mit einem entsprechenden Kommandozeilenparameter aufgerufen werden, um Informationen auszugeben, die hilfreich sind um Anpassungen vorzunehmen.
Wurden letztlich Erkennung und Anpassung durchlaufen, wird das Gesamtergebnis ausgegeben, entweder in Form von MQTT Auto Discovery Topics oder aber als yaml-Datei. Die yaml-Datei kann manuell in die Home Assistant Konfiguration eingebunden werden. In beiden Fällen werden alle Datenpunkte den jeweiligen Geräten zugeordnet. Dies erfolgt nicht über zusätzliche Ausgaben von Metadaten, sondern inline über die jeweilige Homeatic Geräte ID. Im Falle der Ausgabe über einen MQTT Broker, werden standardmnäßig Abkürzungen verwendet, die von der Home Assistant MQTT Integration verstanden werden. Dieses Verhalten kann abgeschaltet werden. Erfolgt die Ausgabe als yaml-Konfiguration, darf man sich von der Länge der Datei nicht erschrecken lassen. Für meine Homematic-Geräte inkl. Systemvariablen und Zentralenprogramme wird eine yaml-Datei mit einem Umfang von über 6500 Zeilen erstellt. Home Assistant benötigt ein wenig um eine Konfiguration dieses Umfangs zu lesen, danach ist aber keine Verlangsamung von Home Assistant feststellbar.


## Voraussetzungen
Jacking2HA benötigt mindestens Python 3.10. Für die Installation der benötigten Module aus requirements.txt ist eine venv-Umgebung empfohlen, wird aber nicht zwangsweise vorausgesetzt.


## Verwendung
```
python jacking2ha [-h] --config CONFIG [-e {all,device,program,sysvar}]

Optionen:

  --config CONFIG, -c CONFIG
                        Pfad und Name zur JSON Konfigurationsdatei

  -e {all,device,program,sysvar}, --enumerate {all,device,program,sysvar}
                        Optional. Gibt Informationen aus, die für die Anpassungen
                        von gefundenen Datenpunkten hilfreich sind
```


## JSON Konfigurationsdatei

#### Abschnitt \'config\'

**Option** | **Beispiel** | **Beschreibung**
--- | --- | ---
"mqttHost" | "mqtt.broker" | Hostname des MQTT Brokers, der von Home Assistant genutzt wird. Sollen keine MQTT Auto Discovery Records erstellt werden, kann als Wert für diese Option sowie für Port, User und Passwort jeweils ein leerer String gesetzt werden
"mqttPort" | "8883" | Port des MQTT Brokers. Sobald ein anderer Port als 1883 gesetzt ist, wird SSL angenommen
"mqttUser" | "username" | Benutzername für die Anmeldung am MQTT Broker
"mqttPass" | "pAssw0rd" | Passwort für die Anmeldung am MQTT Broker
"mqttCaCert" | "root.pem" | Pfad und Dateiname des Root-Zertifikats für SSL-gesicherte Verbindung zum MQTT Broker
"ccuJackUrl" | "https://hmccu3.com:2122" | CCU-Jack URL und Port. Sobald Port 2122 gegeben ist, wird SSL angenommen
"ccuJackUser" | "cheffe" | Benutzername für die Anmeldung an CCU-Jack
"ccuJackPass" | "t0pSicher" | Passwort für die Anmeldung an CCU-Jack
"ccuJackCaCert" | "privnet.xmas.crt.pem" | Pfad und Dateiname des Root-Zertifikats für SSL-gesicherte Verbindung zu CCU-Jack
"ccuJackReadDevice" | true | Boolean. (De-)aktiviert die Erkennung von Homematic-Geräten
"ccuJackReadProgram" | true | Boolean. (De-)aktiviert die Erkennung von Programmen der Homematic-Zentrale
"ccuJackReadSysvar" | true | Boolean. (De-)aktiviert die Erkennung von Variablen der Homematic-Zentrale
"ccuJackReadVirtdev" | true | Boolean. (De-)aktiviert die Erkennung von virtuellen Geräten in CCU-Jack
"ccuJackBaseTopic" | "hmccu3" | MQTT Base Topic unter dem CCU-Jack Datenpunkte veröffentlicht. Wird CCU-Jack selbst als Broker für Home Assistant verwendet, kann ein leerer String angegeben werden. Relevant wird diese Option im Falle einer Bridge zwischen CCU-Jack und einem weiteren MQTT Broker
"haDiscoveryTopic" | "homeassistant" | Discovery Topic der Home Assistant Instanz
"outputToJson" | false | Boolean. (De-)aktiviert die Erstellung einer JSON-Datei nach Erkennung, Verarbeitung und Anpassung der Datenpunkte bzw. Entitäten. Dient lediglich der Übersicht über das Gesamtergebnis
"outputToMqtt" | false | Boolean. (De-)aktiviert die Veröffentlichung der Auto Discovery Einträge
"outputToYaml" | true | Boolean. (De-)aktiviert die Ausgabe einer yaml-Datei für die Einbindung in die Home Assistant Konfiguration
"createMiscEntities" | true | Boolean. Ist die Erkennung von Programmen und/oder Variablen der Homematic-Zentrale aktiviert, kann das Erstellen zusätzlicher yaml-Dateien (de-)aktiviert werden, die dem Starten von Programmen bzw. der Aktualisierung von Variablen dienen
"enumerateRcButtons" | true | Boolean. (De-)aktiviert das Nummerieren von Buttons von (virtuellen) Fernbedienungen.
"mqttAbbreviations" | true | Boolean. (De-)aktiviert die Verwendung von Abkürzungen in den MQTT Auto Discovery Einträgen. Spart Speicher.
"languageId" | 2 | 1 - Englisch, 2 - Deutsch
"debug" | false | Boolean. (De-)aktiviert die Ausgabe aller gefundenen Objekte inkl. aller internen Attributen sofern die Erstellung einer JSON-Ausgabe aktiviert wurde. Wird üblicherweise nicht benötigt.


#### Abschnitt \'itemFilter\'

Liste von Homematic Datenpunkten, die von Jacking2HA erkannt und verarbeitet werden dürfen. Bei einigen Homematic-Geräten existieren gleichnamige Datenpunkten in verschiedenen Kanälen, was durchaus zu Verwirrungen führen kann. Daher kann hier optional jedem Datenpunkt eine Kanalnummer angefügt werden, jeweils durch einen Doppelpunkt getrennt.


#### Abschnitt \'customization\'

Dieser Abschnitt dient dazu, gefundene Datenpunkte bzw. Entitäten anzupassen. Um einen einzelnen Datenpunkt zu addressieren, ist die Angabe von Homematic Device ID, des Kanals und des Names des Datenpunktes erforderlich. Es können beliebige Attribute hinzugefügt werden. Unerwünsche Attribute können durch die Angabe des Werts "-" gelöscht werden.
Anstatt einzelne Datenpunkte zu addressieren, kann als Device ID, Kanal und/oder Name eines Datenpunkts jeweils das Schlüsselwort "~all" angegeben werden. Durch die Angabe von "-" als Wert für Device ID, Kanal oder Name eines Datenpunkts, lassen sich gezielt einzelne Datenpunkte und ganze Kanäle bzw. Geräte von der weiteren Verarbeitung ausschließen. Beispiele in der Datei "jacking2ha.json".


