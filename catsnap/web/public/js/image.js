/* jshint jquery:true, browser:true */

$(document).ready(function() {
  'use strict';

  /*
  * This is basically .load(), except load events happen too soon when the image comes from cache.
  * Looping through the images and manually firing load() is a workaround from stackoverflow:
  * http://stackoverflow.com/a/3877079/1308699
  * using .one('load') avoids a race condition where the load event could fire twice (once automatically,
  * once manually), although it wouldn't be terribly bad in this case.
  */
  $('.image-container img').one('load', function() {
    $('.image-container, .image-container *').css('max-width', $(this).width());
  }).each(function() {
    if (this.complete) {
      $(this).load();
    }
  });

  function startEditing(event) {
    event.preventDefault();
    var $editButton = $(event.target);
    $editButton.text('Stop Editing');
    $('.edit').show();
    $('.view').hide();
    $editButton.off('click');
    $editButton.click(stopEditing);
  }

  function stopEditing(event) {
    event.preventDefault();
    var $editButton = $(event.target);
    $('#image-edit').submit();
    $editButton.text('Edit');
    $('.edit').hide();
    $('.view').show();
    $editButton.off('click');
    $editButton.click(startEditing);
  }

  function saveEdits(event) {
    event.preventDefault();
    var $form = $(event.target),
        formData;

    formData = $.makeArray($form.find('*')).reduce(function(agg, elem) {
      if (elem.name && (typeof elem.value !== 'undefined')) {
        agg[elem.name] = elem.value;
      }
      return agg;
    }, {});

    $.ajax($form.attr('action') + '.json', {
      type: "PATCH",
      data: formData,
      success: function(data) {
        $('#caption').text(data.image.caption);
        if (data.image.description) {
          var paras = data.image.description.split('\n').map(function(line) {
            return $('<p class="image-description view">').text(line);
          });

          $('#image-description').empty().append(paras);
        } else {
          $('#image-description').empty();
        }
      },
      error: window.alert
    });
  }

  function removeTag(event) {
    event.preventDefault();
    var $li = $(event.target).parent(),
        imageId = $li.parents('div.edit').data('image-id'),
        tagName = $li.find('a').text();

    $.ajax('/image/' + imageId + '.json', {
      type: "PATCH",
      data: {
        'remove_tag': tagName,
      },
      success: function(data) {
        $li.remove();
        $('.view li.tag').filter(function(index, element) {return element.textContent === tagName;}).remove();
        if ($('.view li.tag').length === 0) {
          $('#tag-button').addClass('disabled');
        }
      }
    });
  }

  function showTagInput(event) {
    var tagName,
        abortEditing,
        submitTag,
        $addLi = $($(event.target).parents('li')[0]),
        $newLi,
        $tagInput,
        imageId = $addLi.parents('div.edit').data('image-id'),
        $form;
    event.preventDefault();

    submitTag = function submitTag(event, successHandlers) {
      event.preventDefault();
      if (typeof(successHandlers) === 'undefined') {
        successHandlers = [];
      }

      tagName = $tagInput.val().trim();
      if (tagName === '') {
        abortEditing();
        return;
      }

      $form.find('input').attr('disabled', true);

      $.ajax('/image/' + imageId + '.json', {
        type: 'PATCH',
        data: {add_tag: tagName},
        success: [function(data) {
          var $button = $('<button class="btn btn-xs btn-default remove-tag">'),
              $xSign = $('<span class="glyphicon glyphicon-remove-sign" aria-label="remove">'),
              $tag = $('<a href="#" class="remove-tag">'),
              $viewLi = $('<li role="presentation" class="tag"></li>'),
              $tagLink = $('<a role="menuitem">');
          $tag.text(tagName);
          $form.remove();
          $button.append($xSign);
          $newLi.append($button);
          $newLi.append($tag);
          $addLi.show();
          $('#tag-button').removeClass('disabled');


          $tagLink.text(tagName);
          $tagLink.attr('href', "/find?tags=" + tagName);
          $viewLi.append($tagLink);
          $('.view-tags').append($viewLi);
        }].concat(successHandlers),
        error: window.alert
      });
    };

    abortEditing = function abortEditing() {
      /* In Firefox (at least), if there's an autocompletion box up when the input
      is removed, the input goes away correctly but the autocompletion box hangs
      around. Blurring the element first seems to be a sufficient workaround.
      Bug reported: https://bugzilla.mozilla.org/show_bug.cgi?id=1091954
      */
      $tagInput.off('blur');
      $tagInput.blur();
      $newLi.remove();
      $addLi.show();
    };

    $addLi.hide();

    $newLi = $('<li>');
    $form = $('<form><input type="submit" class="enter-to-submit"></form>');
    $tagInput = $('<input type="text" class="edit form-control" name="tag" id="tag">');
    $tagInput.keydown(function(event) {
      if (event.which === window.KeyCodes.TAB) {
        event.preventDefault();
        $form.triggerHandler('submit', function() {
            $addLi.find('a').click();
        });
      } else if (event.which === window.KeyCodes.ESCAPE) {
        abortEditing();
      }
    });
    $tagInput.show();
    $form.submit(submitTag);
    $tagInput.blur(submitTag.bind($form));
    $form.prepend($tagInput);
    $newLi.prepend($form);
    $addLi.before($newLi);
    $tagInput.focus();
  }

  $('#edit').click(startEditing);
  $('#image-edit').submit(saveEdits);
  $('.add-tag').click(showTagInput);
  $(document).on('click', '.remove-tag', removeTag);
});