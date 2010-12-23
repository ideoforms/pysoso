$SCRIPT_ROOT = "/pysoso";

$(function()
{
	$('a#calculate').bind('click', function() {
		$.getJSON($SCRIPT_ROOT + '/_add_numbers', {
			a: $('input[name="a"]').val(),
			b: $('input[name="b"]').val()
		}, function(data) {
			$("#result").text(data.result);
		});
		return false;
	});

	$('html').keypress(function(event)
	{
		if (event.target.tagName == "INPUT")
			return;

		// c: show/hide controls
  		if (event.which == 99)
			$('#controls .bookmarks_show').click();

		// e: toggle editing
  		else if (event.which == 101)
			$('a#edit').click();

		// f: toggle fresh bookmarks
		else if (event.which == 102)
			$('#bookmarks_active .bookmarks_show').click();

		// s: toggle stale bookmarks
		else if (event.which == 115)
			$('#bookmarks_stale .bookmarks_show').click();

		// 1..9: toggle tags
		else if (event.which >= 49 && event.which <= 57)
		{
			index = event.which - 49 + 1;
			tags = $(".tags a:nth-child(" + index + ")").click();
		}
	});

	$('a#edit').bind('click', function () {
		if ($(this).hasClass("active"))
		{
			$(this).removeClass("active");
			$("#bookmarks .tools").hide();
		}
		else
		{
			$(this).addClass("active");
			$("#bookmarks .tools").show();
		}
		return false;
	});

	$('.tag_show').bind('click', function () {
		if ($(this).hasClass("active"))
		{
			var li = $(this).parents("#bookmarks").find("li");
			li.show();
			$(this).removeClass("active");
		}
		else
		{
			var tag = $(this).attr("text");
			var li = $("#bookmarks").find("li[tags~=" + tag + "]");
			document.title = "showing " + li.length;
			li.show();
			li = $(this).parents("#bookmarks").find("li:not([tags~=" + tag + "])");
			li.hide();
			$(this).parents("h2").find(".tag_show").removeClass("active");
			$(this).addClass("active");
		}
	});

	$('.bookmarks_show').bind('click', function () {
		var ul = $(this).parents("div").children("ul");
		if (ul.is(":visible"))
		{
			ul.hide("fast");
			$(this).removeClass("active");
		}
		else
		{
			ul.show("fast");
			$(this).addClass("active");
		}

		return false;
	});

	$('#bookmarks .edit').bind('mouseover', function () {
		var el = $(this).parents("li").find(".link");
		el[0].style.textDecoration = "underline";
	});

	$('#bookmarks .edit').bind('mouseout', function () {
		var el = $(this).parents("li").find(".link");
		el[0].style.textDecoration = "none";
	});

	$('#bookmarks .delete').bind('mouseover', function () {
		var el = $(this).parents("li").find(".link");
		el[0].style.textDecoration = "line-through";
	});

	$('#bookmarks .delete').bind('mouseout', function () {
		var el = $(this).parents("li").find(".link");
		el[0].style.textDecoration = "none";
	});


	$('#bookmarks .delete').bind('click', function () {
		$(this).parents("li").hide("fast");
		$.getJSON($(this).attr("href"));
		return false;
	});

	$('#bookmarks .bookmark').bind('click', function () {
		$(this).parents("li").hide("fast", function () { $(this).remove(); });
	});


});
