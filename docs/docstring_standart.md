```xml
<DOC_STANDARDS>
<DOC_STANDARDS_TITLE>Documentation Standards</DOC_STANDARDS_TITLE>

<DOC_STANDARDS_CONTRACT>
<DOC_STANDARDS_CONTRACT_DESCRIPTION>
Contract is a section related to state restrictions between caller and called methods
Called method - method in which current contract is defined
Caller method - should follow *called* method's contract
It contains sections: `PURPOSE`, `DESCRIPTION`, `ATTRIBUTES`, `ARGUMENTS`, `RETURNS`, `PRECONDITION`, `POSTCONDITION`, `RAISES`.

VERY IMPORTANT:
- there is no other sections! 
- PRECONDITION NEVER describes types of arguments, it NEVER says `subclass of` or `is a valid instance`
- If a subsection (PRECONDITIONS, POSTCONDITIONS, INVARIANTS, FRAME, RAISES) has no items, omit that subsection. 
- If all subsections would be empty, omit the entire CONTRACTS block.
- There is no empty lines between sections

</DOC_STANDARDS_CONTRACT_DESCRIPTION>

<DOC_STANDARDS_CONTRACT_PRECONDITION>
This section describes *state* of arguments from function signature like:
- attribute value ranges
    
IMPORTANT:
- DO NOT describe types that already described in signature
- DO NOT write the same description that already exists in ARGUMENTS block
<DOC_STANDARDS_CONTRACT_PRECONDITION_EXAMPLES>
- self._size equals len(self._items), 
- model.id is immutable once set, 
</DOC_STANDARDS_CONTRACT_PRECONDITION_EXAMPLES>
</DOC_STANDARDS_CONTRACT_PRECONDITION>

<DOC_STANDARDS_CONTRACT_POSTCONDITION>
This section describes *state* of affected objects provided by caller in signature or returned to caller in return.

IMPORTANT:
- DO NOT describe types that already described in signature
- DO NOT write the same description that already exists in RETURNS block
<DOC_STANDARDS_CONTRACT_POSTCONDITION_EXAMPLES>
Returned list is sorted ascending by key.
A file at dst_path exists and is a byte-for-byte copy of src_path.
Exactly one message is published to queue Q with correlation_id == returned_id.
The transaction is committed atomically; all affected rows reflect the new state on success.
The numeric result r satisfies |r - target| ≤ epsilon provided by the caller.
The returned graph is acyclic and includes all vertices reachable from the provided start node.
</DOC_STANDARDS_CONTRACT_POSTCONDITION_EXAMPLES>
</DOC_STANDARDS_CONTRACT_POSTCONDITION>

<DOC_STANDARDS_CONTRACT_RAISES>
List all exceptions that may be raised in the `called` method and the exact situations that trigger them.
Only direct exception counts, explicitly mentioned in method's code
<DOC_STANDARDS_CONTRACT_RAISES_EXAMPLES>
"ValidationError - when email format is invalid", 
"NotFoundError - when user_id does not exist", 
"PermissionError - when caller lacks required role"
</DOC_STANDARDS_CONTRACT_RAISES_EXAMPLES>
</DOC_STANDARDS_CONTRACT_RAISES>

<DOC_STANDARDS_CONTRACT_EXAMPLE>
"""
PURPOSE: Brief one-line statement of functionality
DESCRIPTION: Detailed explanation of behavior and implementation
ATTRIBUTES:
    attribute_name: type - Description of attribute
ARGUMENTS:
    param_name: type - Description of parameter
RETURNS: return_type - Description of return value
CONTRACTS:
    PRECONDITION:
        - DOC_STANDARDS_CONTRACT_PRECONDITION_EXAMPLES
    POSTCONDITION:
        - DOC_STANDARDS_CONTRACT_POSTCONDITION_EXAMPLES
    RAISES:
        - DOC_STANDARDS_CONTRACT_RAISES_EXAMPLES
"""
</DOC_STANDARDS_CONTRACT_EXAMPLE>

<DOC_STANDARDS_CONTRACT_STYLE_GUIDELINES>
<DOC_STANDARDS_CONTRACT_STYLE_GUIDELINES_1>
Write each contract item as a concise, testable statement in present tense
</DOC_STANDARDS_CONTRACT_STYLE_GUIDELINES_1>
<DOC_STANDARDS_CONTRACT_STYLE_GUIDELINES_2>
- Prefer measurable predicates (e.g., "non-empty", "RFC 3986 URI", "timezone-aware") over vague terms like "valid" or "proper"
</DOC_STANDARDS_CONTRACT_STYLE_GUIDELINES_2>
<DOC_STANDARDS_CONTRACT_STYLE_GUIDELINES_3>
- Avoid duplication across ARGUMENTS/RETURNS and CONTRACTS; one fact belongs in one place only
</DOC_STANDARDS_CONTRACT_STYLE_GUIDELINES_3>
<DOC_STANDARDS_CONTRACT_STYLE_GUIDELINES_4>
- Use precise technical language appropriate for backend systems
</DOC_STANDARDS_CONTRACT_STYLE_GUIDELINES_4>
<DOC_STANDARDS_CONTRACT_STYLE_GUIDELINES_5>
- Focus on behaviors that are checkable without causing side effects (for PRE) or observable after success (for POST)
</DOC_STANDARDS_CONTRACT_STYLE_GUIDELINES_5>
</DOC_STANDARDS_CONTRACT_STYLE_GUIDELINES>
</DOC_STANDARDS_CONTRACT>

<DOC_STANDARDS_ELEMENT_REQUIREMENTS>
<DOC_STANDARDS_ELEMENT_REQUIREMENTS_TITLE>Element-Specific Requirements</DOC_STANDARDS_ELEMENT_REQUIREMENTS_TITLE>
    
<DOC_STANDARDS_CLASSES>
<DOC_STANDARDS_CLASSES_REQUIREMENTS>
<DOC_STANDARDS_CLASSES_REQUIRED_SECTIONS>Include PURPOSE, DESCRIPTION, ATTRIBUTES</DOC_STANDARDS_CLASSES_REQUIRED_SECTIONS>
</DOC_STANDARDS_CLASSES_REQUIREMENTS>
</DOC_STANDARDS_CLASSES>

<DOC_STANDARDS_METHODS>
<DOC_STANDARDS_METHODS_REQUIREMENTS>
<DOC_STANDARDS_METHODS_REQUIRED_SECTIONS>Include PURPOSE, DESCRIPTION, ARGUMENTS (excluding `self`), RETURNS</DOC_STANDARDS_METHODS_REQUIRED_SECTIONS>
<DOC_STANDARDS_METHODS_REQUIREMENT_CONTRACTS>Include CONTRACTS with PRECONDITION/POSTCONDITION/RAISES</DOC_STANDARDS_METHODS_REQUIREMENT_CONTRACTS>
<DOC_STANDARDS_METHODS_REQUIREMENT_SIDE_EFFECTS>Explain side effects and state changes within the class context</DOC_STANDARDS_METHODS_REQUIREMENT_SIDE_EFFECTS>
</DOC_STANDARDS_METHODS_REQUIREMENTS>
</DOC_STANDARDS_METHODS>

<DOC_STANDARDS_FUNCTIONS>
<DOC_STANDARDS_FUNCTIONS_REQUIREMENTS>
<DOC_STANDARDS_FUNCTIONS_REQUIRED_SECTIONS>Include PURPOSE, DESCRIPTION, ARGUMENTS, RETURNS</DOC_STANDARDS_FUNCTIONS_REQUIRED_SECTIONS>
<DOC_STANDARDS_FUNCTIONS_REQUIREMENT_CONTRACTS>Include CONTRACTS with PRECONDITION/POSTCONDITION/RAISES</DOC_STANDARDS_FUNCTIONS_REQUIREMENT_CONTRACTS>
<DOC_STANDARDS_FUNCTIONS_REQUIREMENT_EXCEPTIONS>Document any exceptions or special behaviors</DOC_STANDARDS_FUNCTIONS_REQUIREMENT_EXCEPTIONS>
</DOC_STANDARDS_FUNCTIONS_REQUIREMENTS>
</DOC_STANDARDS_FUNCTIONS>
</DOC_STANDARDS_ELEMENT_REQUIREMENTS>
</DOC_STANDARDS>
```
