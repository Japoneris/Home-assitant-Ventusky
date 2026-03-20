# Ventusky Scrapper + Home Assistant Integration

![](custom_components/ventusky/brand/icon.png)


This custom Home Assistant component lets you get current weather and forecast from [Ventusky](https://www.ventusky.com).

The tool scrap the ventusky html web page, so you do not need any API key for configuring the component.

Because we scrap the webpage, the app can break at any time if the Ventusky UI is changed.
Please let me know if you encounter any issue.


## Configuration

First, you need to get this component refistered, either through HACS or by cloning this repo.

For local configuration, move the `custom_components/ventusky` in your Home assisitant `custom_components/` folder.


## Addint a widget

On your Home Assistant interfact, click on "Add a device". 
Then search for "Ventusky Weather".

You will be asked for 4 things:

- longitude,
- latitude,
- place name (this in only for display)
- refresh interval in minutes (By default, 60 minutes, but you can put less. Avoid refreshing too frequently to avoid any ban from the weather server).

**How to get your latitude/longitude?**

1. Go on the official [Ventusky Website](https://www.ventusky.com/)
2. Search for your city
3. Click on the map on the dot representing the city. You should have a right pannel with the forecast.
4. On the URL, you should have two numbers, like `https://www.ventusky.com/<lat>;<long>`.
5. Provide to the widget these values

Then, validate. The widget is configured.

## Lovelace Card

To setup the lovelace card, please have a look at [INSTALL.md](INSTALL.md)


## Customization

If you want to customize this app, please have a look at the [local](local/readme.md) folder, where you have the raw scripts extracting the information from the webpage.

