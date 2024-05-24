# Argo Umbrella Chart

Installation of ArgoCD with Helm using the [app-of-apps](https://argo-cd.readthedocs.io/en/stable/operator-manual/declarative-setup/#app-of-apps) pattern, set Argo CD up so that it can update itself, and install Prometheus and Istio via Argo CD as examples.

## Requirements
To follow this tutorial, you'll need the following:

- A Kubernetes cluster (1.28)
- kubectl (1.28)
- Helm (3.13)
- A public git repository (for Argo CD to pull the manifests)

Our application manifests will be stored in a public Git repository. For this tutorial I'm using GitHub, but this can be any public Git repository, and GitLab, Gitea, etc. work just as well.

## Structure

```
charts/argo-cd/Chart.yaml
```

In this file you can setting the version of our custom chart. The version of the dependency matters and if you want to upgrade the chart, would be the place to do it. The important thing is that we pull in the community-maintained argo-cd chart as a dependency.

Next, create a values.yaml file for our chart:
```
charts/argo-cd/values.yaml
```

To override the chart values of a dependency, we have to place them under the dependency name. Since our dependency in the Chart.yaml is called argo-cd, we have to place our values under the argo-cd: key. If the dependency name would be abcd, we'd place the values under the abcd: key.

All available options for the Argo CD Helm chart can be found in the values.yaml file.

We use a rather minimal installation, and disable components that are not useful for this tutorial. The changes are:

- Disable the dex component (integration with external auth providers).
- Disable the notifications controller (notify users about changes to application state).
- Disable the ApplicationSet controller (automated generation of Argo CD Applications).
- We start the server with the --insecure flag to serve the Web UI over HTTP. For this tutorial, we're using a local k8s server without TLS setup.

Before we install our chart, we need to generate a Helm chart lock file for it. When installing a Helm chart, Argo CD checks the lock file for any dependencies and downloads them. Not having the lock file will result in an error.

```
$ helm repo add argo-cd https://argoproj.github.io/argo-helm
$ helm dep update charts/argo-cd/
```

## Installing Helm chart

```
$ kubectl create namespace argo-cd monitor
$ helm install argo-cd charts/argo-cd/ --namespace argo-cd
```

## Accessing the Web UI

```
$ kubectl port-forward svc/argo-cd-argocd-server 8080:443
```

We can then visit http://localhost:8080 to access it, which will show as a login form. The default username is admin. The password is auto-generated, we can get it with:

```
$ kubectl get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

## Creating the root-app Helm chart

```
helm template root-app/ | kubectl apply -f -
```

As a last step, we can remove the Secret that Helm creates for each manual chart installation:

```
$ kubectl delete secret -l owner=helm,name=argo-cd
```


## Uninstall argocd

```
kubectl patch customresourcedefinitions.apiextensions.k8s.io applications.argoproj.io -p '{"metadata":{"finalizers":[]}}' --type=merge
kubectl delete customresourcedefinitions.apiextensions.k8s.io applications.argoproj.io
kubectl delete customresourcedefinitions.apiextensions.k8s.io appprojects.argoproj.io
helm uninstall argo-cd --namespace argo-cd
```


# Reference
[Setting up Argo CD with Helm](https://www.arthurkoziel.com/setting-up-argocd-with-helm/)
