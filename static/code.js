
// h2, h3, h4 tags
var documentHeadings = [];

// The currently selected heading element (in content div, not menu)
// we keep track of it to detect if it's outside the visible area.
var currentHeadingElement = null;

// The a elements in the left menu refering 
// to the above elements in the document
var menuHeadings = [];

function isElementInViewport (el) {
    var rect = el.getBoundingClientRect();

    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.body.clientHeight) && 
        rect.right <= (window.innerWidth || document.body.clientWidth)
    );
}

function getFirstVisibleHeading() {
    for(var i=0;i<documentHeadings.length;i++) {
        var el = documentHeadings[i];
        if(isElementInViewport(el))
            return el;
    }
}

// Decompose url
function parseUrl(str)
{
    var url = {};
    var s = str.split('/');
    url.filename = s[s.length-1];
    
    if(url.filename.indexOf('#') != -1) {
        var s2 = url.filename.split('#');
        url.filename = s2[0];
        url.id = s2[1];
    }
    return url;
}

function jumpToId(id)
{
    var subtitleEl = document.getElementById(id);
    console.log(subtitleEl);
    var top = subtitleEl.offsetTop;

    // The entire point of this is that we adjust the scroll position with the offset below
    // to avoid obscuring the view with the menu which is overlayed.
    var adjust = 75;

    // To override autoscroll
    // Maybe use pseudo id for subtitles instead, won't work without js then though.
    // It's still a bit janky when loading because it first autoscrolls then jumps to "correct" position.
    setTimeout(function() {
        document.body.scrollTop = top - adjust;
      }, 1);
    window.location.hash = id;
}

function clickSubtitle(e)
{
    docUrl = parseUrl(document.URL);
    clickedUrl = parseUrl(e.target.getAttribute('href'));

    // not the same page, let's just follow the link.
    if(clickedUrl.filename != docUrl.filename) {
        return true;
    }
    
    jumpToId(clickedUrl.id);
    selectHeading(clickedUrl.id);

    e.preventDefault();
    return false;
}

/* Get a <h> element from #content */
function getContentHeading(id) {
    for(var i=0;i<documentHeadings.length;i++) {
        if(documentHeadings[i].getAttribute('id') == id)
            return documentHeadings[i];
    }
}

// Marks the heading in the list and unselects everything else.
function selectHeading(id) {
    for(var i=0;i<menuHeadings.length;i++)
    {
        var el = menuHeadings[i];
        el.classList.remove('selected');
        url = parseUrl(el.getAttribute('href'));
        if(url.id == id) {
            el.classList.add('selected');
            currentHeadingElement = getContentHeading(id);
        }
    }
}

document.addEventListener("DOMContentLoaded", function(event) {
    
    docUrl = parseUrl(document.URL);
    // Run only x times every sec maybe? Could impact perf in a massive document.
    document.body.addEventListener("scroll", function(event) {
        if(!isElementInViewport(currentHeadingElement)) {
            var el = getFirstVisibleHeading();
            if(el != null)
                selectHeading(el.getAttribute('id'));
        }
    });

    for(var i=0;i<document.getElementById('content').childElementCount; i++) {
        var ch = document.getElementById('content').children[i];
        var tag = ch.tagName.toLowerCase();
        if(tag == 'h2' || tag == 'h3' || tag == 'h4')
            documentHeadings.push(ch);
    }
    
    menuHeadings = document.getElementsByClassName('subtitle');
    for(var i=0;i<menuHeadings.length;i++)
    {
        menuHeadings[i].onclick = function(e) { return clickSubtitle(e) };
    }

    if(docUrl.id != null) {
        console.log('Jumping to id ' + docUrl.id);
        jumpToId(docUrl.id);
        selectHeading(docUrl.id);
    }

});