jQuery(function(){
    var elements = {  
        navlinks: jQuery('ul.navlinks > li > a[href][title]')
    };
    
    elements.navlinks.qtip({
        position: {
            corner: {
                target: 'bottomMiddle',
                tooltip: 'topMiddle'
            }
        },
        content: {
            text: false
        },
        style: {
            fontFamily: '"Lucida Grande", "Corbel", "Lucida Sans Unicode", "Lucida Sans", "DejaVu Sans", "Bitstream Vera Sans", "Liberation Sans", "Verdana", "Verdana Ref", "sans-serif"',
            border: {
                radius: 5,
                width: 0
            },
            name: 'dark',
            tip: 'topMiddle'
        },
        show: {
            delay: 5
        }
    });
});
