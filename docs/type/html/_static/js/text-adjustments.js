/*
* Modifies header in menu and title. This code strips out "spyglass.xxx".
* It needs to be modified if the naming convention changes or we move off furo-theme
* 
*/

// modified from - https://stackoverflow.com/a/26188910/178550
const camelPad = (str) => { 
    return str
        // Look for long acronyms and filter out the last letter
        .replace(/([A-Z]+)([A-Z][a-z])/g, ' $1 $2')
        // Look for lower-case letters followed by upper-case letters
        .replace(/([a-z\d])([A-Z])/g, '$1 $2')
        // Look for lower-case letters followed by numbers
        .replace(/([a-zA-Z])(\d)/g, '$1 $2')
        .replace(/^./, function(str){ return str.toUpperCase(); })
        // Remove any white space left around the word
        .trim();
}

const titleCase = (title) => {
    return !title || !title.trim || title.trim() === '' 
        ? ''
        : title.trim().replace(/\w\S*/g, (w) => (w.replace(/^\w/, (c) => c.toUpperCase())));
}

const removeSpyglassInfo = (text) => {
    if (!text || !text.trim || text.trim() === '') {
        return text;
    }

    const splitText = text.split('.');
    let mainText = splitText.at(-1);
    mainText = mainText.replace('common', '');
    mainText = camelPad(mainText);

    return mainText;
};

const replaceUnderscoreWithWhitespace = (text) => {
    return text?.replaceAll('_', ' ');
};

// Menu
// side menu
{
     const elements = document.querySelectorAll('.toctree-l3 a');

    elements.forEach((element) => {
        // get around issue of javascript lint disliking directly modifying forEach iterator
        const htmlElement = element;
        
        let menuText = element?.text;
        menuText = removeSpyglassInfo(menuText);
        menuText = replaceUnderscoreWithWhitespace(menuText);
        menuText = titleCase(menuText);
        htmlElement.text = menuText;
    });
}

//headers
// on top of API pages
{
    const headerElement = document.querySelector('[role="main"] h1');
    let headerText = headerElement?.textContent;
    headerText = removeSpyglassInfo(headerText);
    headerText = replaceUnderscoreWithWhitespace(headerText);
    headerText = titleCase(headerText);
    headerText = headerText.replace('#', '');

    headerElement.textContent = headerText;
}

// Bottom navigation pages
// The next and previous menus on bottom of API pages
{
    const bottomNavElements = document.querySelectorAll('.page-info .title');

    bottomNavElements.forEach((bottomNavElement) => {
        const element = bottomNavElement;
        let title = bottomNavElement?.textContent;

        // display "spyglass.common" if the menu option is that
        if (title !== 'spyglass.common') {
            title = removeSpyglassInfo(title);
            title = replaceUnderscoreWithWhitespace(title);
            title = titleCase(title);
            title = title.replace('#', '');
        }
        element.textContent = title;
    });
}
