# tdskit

query your sqlserver instance directly from sublime text 3


## Requirement

* python 3.5
* [wxPython 4]( https://wxpython.org/)
* [pytds](https://github.com/denisenkom/pytds)

## Installation 

Tdskit is composed of 2 modules:
* A service module running as a server
* A sublime text plugin

### Service

[pytds](https://github.com/denisenkom/pytds#installation)

```
pip install python-tds
```
Optionaly:
```
pip install pyOpenSSL
pip install bitarray
```

[wxPython](https://pypi.org/project/wxPython/4.0.3/)
```
pip install wxPython==4.0.3
```

### Sublime text plugin

#### Manual instalation
Copy the plugin/tdskit in your sublime text package directory (Preferences -> Browse packages)

#### Package control
Todo

## Getting started

Configure your prefered connection in tdskit.sublime-settings (Preferences -> Package setting -> tdskit -> Setting User)

You can use the default configuration as a starting point:
```javascript
{ 
	// Available connection list
	"Connections": 
	[
		{
			// Name of the connection, so you can easily identify them
			"Name": "Production server 1"
			, "Server": "ProdServerName"
			// Instance name
			, "Instance" : "ProdInstanceName"
			// Default database 
			, "DefaultDatabase" : "Customer"
			// If no username is specified, Windows authentication is used
			},
		{
			"Name": "UAT server 2"
			, "Server": "Carlos"
			,"Instance" : "Uat1"
			, "User" : "testUser"
			, "Password" : "xxxxxx"
		}
	]
}
```

Start the service process
```
python service.py
```

Now you're ready to go.

| ShortCut     | Command                                                      |
|--------------|--------------------------------------------------------------|
| ctrl+f5      | Connect to a server                                          |
| f5           | Execute                                                      |
| f12          | Script the selected view/fuction/procedure in a new window   |
| ctrl+f1      | sp_help the selected object                                  |


