(function($){
    $(function(){
        /*var article_template_string = [
            '<li class="article">',
            '<span class="date">${human_date}</span>',
            '<h1 class="title">${title}</h1>',
            '<h2 class="authorline">${author_nickname}</h2>',
            '<div class="article-content">${content_html}</div>',
            '</li>'
        ].join('');
        var article_template = $.template(article_template_string);
        var d = new Date();
        var current_year = d.getFullYear();
        var current_month = d.getMonth() + 1;
        var BLOG_DATE_FORMAT = 'd MMM';
        var showdown = new Showdown.converter();

        function show_articles(articles, textStatus){
            if (textStatus == 'success'){
                var container = $('ul#articles');
                container.empty();
                $.each(articles, function(index, article){
                    article.content_html = showdown.makeHtml(article.content);
                    article.human_date = Date.parse(article.when_published).toString(BLOG_DATE_FORMAT);
                    container.append(article_template, article);
                });
            }
        }
        var $month_drop_down = $('#form_blog_archives select[name="month"]');
        var $year_drop_down = $('#form_blog_archives select[name="year"]');

        function get_articles(e){
            $.getJSON('/json/blog/', {
                'year': $year_drop_down.val(),
                'month': $month_drop_down.val()
            }, show_articles);
        }
        $year_drop_down.val(current_year).change(get_articles);
        $month_drop_down.val(current_month).change(get_articles);
        $('#form_blog_archives').submit(function(e){
            $.getJSON('/json/blog/', $(this).serialize(), show_articles);
            return false;
        });
        $.getJSON('/json/blog/', {
            'year': current_year,
            'month': current_month
        }, show_articles);
        */

        /* Books */
        $('a[rel="#books_overlay"]').overlay({
            expose: '#444444'
        });
        var overlay = $('#books_overlay').overlay({
            expose: '#444444',
            api: true
        });
        $('li.book-cover').live('click', function(e){
            overlay.load();
            e.preventDefault();
            e.stopPropagation();
            return false;
        });
        $.getJSON('/json/books/', {}, function(books, textStatus){
            if (textStatus == 'success'){
                var sidebar_books = books.slice(0, 10);
                var html = [];
                var sidebar_html = [];
                $.each(books, function(index, book){
                    html.push(['<li id="',
                        book.key,
                        '"><img height="60" src="http://covers.openlibrary.org/b/isbn/',
                        book.isbn_13,
                        '-M.jpg" /><h1>',
                        book.title,
                        ' <a class="info" target="_blank" href="',
                        book.info_url,
                        '">info</a></h1><h2>',
                        '</h2></li>'
                    ].join(''));
                });
                $.each(sidebar_books, function(index, book){
                    sidebar_html.push(['<li class="book-cover">',
                        '<a href="#books_overlay" rel="#books_overlay">',
                        '<img height="60" src="http://covers.openlibrary.org/b/isbn/',
                        book.isbn_13,
                        '-M.jpg" ><h1>',
                        book.title,
                        '</h1><h2>',
                        book.authors,
                        '</h2></a></li>'
                    ].join(''));
                });
                var books_html = ['<h1>Books you can buy</h1>',
                    '<p id="order_notification">Click any books to select them.</p><ul>',
                    html.join(''),
                    '</ul>',
                    '<a href="#buy_now" id="buy_now"></a>'
                ].join('');
                $('#books_overlay').append(books_html);
                $('#bookers_corner > ul.book-list').html(sidebar_html.join(''));
                $('#order_notification').show('slow');
            }
        });
        $('#books_overlay ul li').live('click', function(e){
            var li = $(this);
            li.fadeTo(100, 0.2).toggleClass('selected').fadeTo('slow', 1);
        });
        $('a#buy_now').live('click', function(e){
            e.stopPropagation();
            e.preventDefault();

            var keys = [];
            $('#books_overlay ul li.selected').each(function(index, elem){
                keys.push($(elem).attr('id'));
            });
            if (keys.length){
                var json_keys = JSON.stringify(keys);
                $.post('/json/books/buy/', {'keys': json_keys}, function(data, textStatus){
                    $('#order_notification').fadeTo('slow', 0, function(){
                        $(this).html('We have requested the vendor to get in touch with you.  Please check your email.').fadeTo('slow', 1);
                    });
                });
            } else {
                $('#order_notification').fadeTo('slow', 0, function(){
                   $(this).html('Please select books by clicking them first.').fadeTo('slow', 1);
                });
            }
            return false;
        });
    });
})(jQuery);

