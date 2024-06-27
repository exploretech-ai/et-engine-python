# ET-Engine

The backend behind The Engine. Components include:

- The master relational database
- A managed Cognito User Pool
- Templates for Tools and VFS
- The compute cluster
- The API

# Using CDK

Note that there are 3 environments: `dev`, `stage`, and `prod`. Use only `dev` when making changes, and then when you're ready for prime time you can switch to prod. To deploy changes to `dev` use the following command:

```
cdk deploy --all -c env=dev
```

and similarly for `stage` and `prod` use 

```
cdk deploy --all -c env=stage
cdk deploy --all -c env=prod
```