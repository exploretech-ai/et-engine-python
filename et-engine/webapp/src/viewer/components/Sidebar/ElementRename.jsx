import React, {useState, useRef, useEffect} from "react";

function ElementRename({initLabel, checkboxProps, checkboxPropsSetter}) {
  const inputRef = useRef(null)
  const [inputValue, setInputValue] = useState(checkboxProps.label)

  // Handles focus on initial rendera
  useEffect(() => {
      inputRef.current.select()
      inputRef.current.focus();
  }, [inputRef]);

  // Saves label once enter is pressed
  function enterPressed(event) {
      const code = event.keyCode || event.which;

      // 13 is the enter keycode
      if(code === 13) { 

          // Update label and remove text input
          let newProps = checkboxProps.clone()
          newProps.label = inputValue
          newProps.renaming = false
          checkboxPropsSetter(newProps)
      } 
  }

  // Handles text change
  function updateInputValue(evt) {
      const val = evt.target.value;
      setInputValue(val)
  }

  // Enforces focus until enter is pressed
  function removeFocus() {
      inputRef.current.focus()
  }

  return (
    <input
      key={initLabel}
      id={initLabel}
      type="text"
      ref={inputRef}  
      onKeyUp={enterPressed}
      onBlur={removeFocus}
      // onFocus={(e) => e.stopPropagation()}
      value={inputValue} 
      onChange={evt => updateInputValue(evt)}
    />
  );
}

export default ElementRename