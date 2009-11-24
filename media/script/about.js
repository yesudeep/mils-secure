/*jQuery(function(){
   
    jQuery(function(){
    /*jQuery("#about_alumni").innerfade({
      animationtype: 'fade',
      speed: 'slow',
      timeout: 12000,
      type: 'sequence',
      containerheight: '250px'
});*/

jQuery(function(){
    /*jQuery("#slider").easySlider({
        numeric: true,
        speed: 200
    });
    jQuery('#items').scrollable({size: 1}).navigator({
        navi: "item_numbers",
        naviItem: 'a',
        activeClass: 'current'
    });*/
    jQuery("#item_numbers").tabs("#items > li", {
          effect: 'horizontal',
          //fadeOutSpeed: "slow",
          rotate: true
    }).slideshow({
          autoplay: true        
    });
});
